"""ReAct-style JSON action loop.

1. Prompt that describes goal, the available
   tools, and the JSON schema needs to produce.
2. The agent runs in a loop — each turn the LLM outputs a JSON object with
   an ``action`` and ``action_input``:
       Thought  → decide what information is still missing
       Action   → {"action": "search_youtube", "action_input": {"query": "..."}}
       Observe  → we execute the tool and feed results back
       …repeat until the agent outputs {"action": "finish", ...}
    Decides which tools to call based on the syllabus content.
    Self-evaluation by checking coverate of topic before finishing.
    Triggers differen searches based on subject domain
3.Parse the final JSON into a ``ResourceRecommendations`` Pydantic model.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time

from openai import OpenAI

from app.models.schemas import (
    ParsedSyllabus,
    ResourceRecommendations,
    StudyPlan,
)
from app.services.resource_tools import TOOL_DISPATCH

logger = logging.getLogger(__name__)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_FALLBACK_MODEL = "llama-3.1-8b-instant"
MAX_AGENT_TURNS = 8  # safety cap so we don't loop forever

RESOURCE_AGENT_SYSTEM_PROMPT = """\
You are an expert academic resource curator agent. Your job is to find the
BEST study resources for a university course by searching the web.

You have access to these tools:
- search_web(query): general web search
- search_youtube(query): find educational YouTube videos
- search_academic(query): search MIT OCW, OpenStax, Coursera, Khan Academy, edX
- search_practice(query): find practice problems on LeetCode, Brilliant, etc.

STRATEGY:
1. First, identify the subject domain and 3-5 key topics from the syllabus.
2. For EACH key topic, use 1-2 tools to find relevant resources.
   - For conceptual topics → search_youtube + search_academic
   - For problem-solving topics → search_practice + search_web
   - For writing/research → search_web + search_academic
3. After searching, evaluate: do you have at least 2-3 good resources per
   topic? If not, search again with a refined query.
4. When you have enough, use action "finish" to output your final answer.

RESPONSE FORMAT — you MUST respond with a JSON object on every turn:

To call a tool:
{"thought": "I need to find videos about ...", "action": "search_youtube", "action_input": {"query": "linear algebra eigenvalues tutorial"}}

To finish (after collecting enough resources):
{"thought": "I have enough resources for all topics.", "action": "finish", "action_input": <FINAL_JSON>}

Where <FINAL_JSON> matches this schema:
{
  "course_name": "string",
  "subject_domain": "string (e.g. mathematics, computer_science, biology)",
  "general_resources": [
    {
      "title": "string",
      "url": "string or null",
      "resource_type": "video|textbook|practice|article|tool|course",
      "platform": "string (e.g. Khan Academy, YouTube, MIT OCW)",
      "relevance": "string (why this resource helps)",
      "priority": "high|medium|low"
    }
  ],
  "topic_resources": [
    {
      "topic": "string",
      "related_events": ["string (titles of related syllabus events)"],
      "resources": [ ...same shape as above... ]
    }
  ],
  "study_tips": ["string (1-3 actionable study tips for this course)"]
}

IMPORTANT RULES:
- Only include resources you actually found via tool searches — use REAL URLs
  from the search results, not made-up ones.
- Aim for 2-4 resources per topic and 2-3 general resources.
- Prioritize FREE resources.
- Be efficient — don't search for the same thing twice.
- You MUST call finish to complete your task.
- ONLY output valid JSON. No markdown, no extra text.
"""


def _get_client() -> OpenAI:
    api_key = os.environ["GROQ_API_KEY"]
    return OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)


def _build_user_prompt(parsed: ParsedSyllabus) -> str:
    """Summarise the syllabus so the agent knows what to search for."""
    lines = [
        f"Course: {parsed.course_name}",
        f"Semester: {parsed.semester}",
        "",
        "Syllabus events:",
    ]
    for e in parsed.events:
        line = f"- {e.title} ({e.event_type}) — {e.date}"
        if e.description:
            line += f" — {e.description}"
        lines.append(line)

    lines.append("")
    lines.append(
        "Find the best study resources for the key topics in this course. "
        "Search for videos, textbooks, practice problems, and articles. "
        "Respond with a JSON action object."
    )
    return "\n".join(lines)


def _extract_json(text: str) -> dict | None:
    """Try to extract a JSON object from the LLM's response text."""
    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code fence
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding the first { ... } block
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    start = None

    return None


def _execute_action(action: str, action_input: dict) -> str:
    """Dispatch an action to the matching Python tool function."""
    fn = TOOL_DISPATCH.get(action)
    if fn is None:
        return json.dumps({"error": f"Unknown tool: {action}. Use one of: search_web, search_youtube, search_academic, search_practice, finish"})
    try:
        if action == "finish":
            return json.dumps(action_input)
        query = action_input.get("query", "")
        if not query:
            return json.dumps({"error": "Missing 'query' in action_input"})
        return fn(query=query)
    except Exception as exc:
        logger.warning("Tool %s raised: %s", action, exc)
        return json.dumps({"error": str(exc)})


def recommend_resources(
    parsed: ParsedSyllabus,
    plan: StudyPlan | None = None,
) -> ResourceRecommendations:
    """Run the agentic resource-routing loop.

    Parameters
    ----------
    parsed : ParsedSyllabus
        Extracted syllabus data (course name, events, etc.).
    plan : StudyPlan | None
        Optional study plan — currently unused but available for future
        enhancements where the agent considers study-block context.

    Returns
    -------
    ResourceRecommendations
        Validated Pydantic model with per-topic resources.
    """
    client = _get_client()
    model = GROQ_MODEL

    messages: list[dict] = [
        {"role": "system", "content": RESOURCE_AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": _build_user_prompt(parsed)},
    ]

    for turn in range(MAX_AGENT_TURNS):
        logger.info("Resource agent — turn %d", turn + 1)

        # Rate-limit pause (Groq free tier)
        if turn > 0:
            time.sleep(3)

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.3,
            )
        except Exception as exc:
            logger.warning("Groq API error with %s: %s — trying fallback", model, exc)
            if model == GROQ_MODEL:
                model = GROQ_FALLBACK_MODEL
                time.sleep(2)
                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        response_format={"type": "json_object"},
                        temperature=0.3,
                    )
                except Exception as exc2:
                    logger.error("Fallback model also failed: %s", exc2)
                    raise
            else:
                raise

        content = response.choices[0].message.content or ""
        messages.append({"role": "assistant", "content": content})

        parsed_json = _extract_json(content)
        if parsed_json is None:
            logger.warning("Could not parse JSON from agent response, asking to retry")
            messages.append({
                "role": "user",
                "content": "Your response was not valid JSON. Please respond with a JSON object containing 'action' and 'action_input'.",
            })
            continue

        action = parsed_json.get("action", "")
        action_input = parsed_json.get("action_input", {})
        thought = parsed_json.get("thought", "")

        if thought:
            logger.info("  Agent thought: %s", thought[:120])

        # If the agent wants to finish
        if action == "finish":
            logger.info("Agent called finish() — parsing recommendations")
            # action_input is the final recommendations payload
            if isinstance(action_input, str):
                return _parse_recommendations(action_input, parsed.course_name)
            return _parse_recommendations(json.dumps(action_input), parsed.course_name)

        # Execute the tool and feed observation back
        if isinstance(action_input, str):
            action_input = {"query": action_input}

        logger.info("  Action: %s(%s)", action, action_input.get("query", "")[:80])
        observation = _execute_action(action, action_input)

        # Truncate large observations to save tokens
        if len(observation) > 3000:
            observation = observation[:3000] + "\n... (results truncated)"

        messages.append({
            "role": "user",
            "content": f"Tool result for {action}:\n{observation}\n\nContinue with the next action or call finish if you have enough resources.",
        })

    # Fallback: try to extract recommendations from the conversation
    logger.warning("Agent exhausted %d turns without calling finish()", MAX_AGENT_TURNS)
    for msg in reversed(messages):
        content = msg.get("content", "") if isinstance(msg, dict) else ""
        if content and "topic_resources" in content:
            parsed_json = _extract_json(content)
            if parsed_json and "topic_resources" in parsed_json:
                return _parse_recommendations(json.dumps(parsed_json), parsed.course_name)

    # Ultimate fallback — return an empty-but-valid object
    return ResourceRecommendations(
        course_name=parsed.course_name,
        subject_domain="unknown",
        general_resources=[],
        topic_resources=[],
        study_tips=["Upload your syllabus and try again for personalized recommendations."],
    )


def _parse_recommendations(raw_json: str, course_name: str) -> ResourceRecommendations:
    """Parse the agent's finish() payload into a validated model."""
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        match = re.search(r"```(?:json)?\s*(.*?)```", raw_json, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
        else:
            raise

    data.setdefault("course_name", course_name)
    data.setdefault("subject_domain", "general")
    data.setdefault("general_resources", [])
    data.setdefault("topic_resources", [])
    data.setdefault("study_tips", [])

    return ResourceRecommendations(**data)
