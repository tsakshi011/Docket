"""Agentic resource-routing engine using a ReAct-style tool-calling loop.

How it works
------------
1. We build a system prompt that describes the agent's goal and the JSON
   schema it must ultimately produce.
2. We give the LLM access to *tools* (search_web, search_youtube,
   search_academic, search_practice, finish) via Groq's function-calling API.
3. The agent runs in a loop:
       Thought  → decide what information is still missing
       Action   → call one or more tools to gather it
       Observe  → read the tool results
       …repeat until the agent calls `finish(recommendations_json)`
4. We parse the final JSON into a `ResourceRecommendations` Pydantic model.

This is what makes the agent *agentic*:
  • It autonomously decides WHICH tools to call based on the syllabus content
  • It iterates — if a search returns poor results it can try a different query
  • It self-evaluates — it checks coverage per topic before finishing
  • It dynamically routes — a math syllabus triggers different searches than
    a history syllabus
"""

from __future__ import annotations

import json
import logging
import os
import time

from openai import OpenAI

from app.models.schemas import (
    ParsedSyllabus,
    ResourceRecommendations,
    StudyPlan,
)
from app.services.resource_tools import TOOL_DEFINITIONS, TOOL_DISPATCH

logger = logging.getLogger(__name__)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "llama-3.3-70b-versatile"
MAX_AGENT_TURNS = 10  # safety cap so we don't loop forever

RESOURCE_AGENT_SYSTEM_PROMPT = """\
You are an expert academic resource curator agent. Your job is to find the
BEST study resources for a university course by searching the web.

You have access to these tools:
- search_web: general web search
- search_youtube: find educational YouTube videos
- search_academic: search MIT OCW, OpenStax, Coursera, Khan Academy, edX
- search_practice: find practice problems on LeetCode, Brilliant, etc.
- finish: call this when you have enough resources for every topic

STRATEGY:
1. First, identify the subject domain and 3-5 key topics from the syllabus.
2. For EACH key topic, use 1-2 tools to find relevant resources.
   - For conceptual topics → search_youtube + search_academic
   - For problem-solving topics → search_practice + search_web
   - For writing/research → search_web + search_academic
3. After searching, evaluate: do you have at least 2-3 good resources per
   topic? If not, search again with a refined query.
4. When you have enough, call finish() with a JSON string matching this schema:

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
- You MUST call finish() to complete your task.
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
        "Then call finish() with your recommendations."
    )
    return "\n".join(lines)


def _execute_tool_call(name: str, arguments: dict) -> str:
    """Dispatch a tool call to the matching Python function."""
    fn = TOOL_DISPATCH.get(name)
    if fn is None:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        return fn(**arguments)
    except Exception as exc:
        logger.warning("Tool %s raised: %s", name, exc)
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

    messages: list[dict] = [
        {"role": "system", "content": RESOURCE_AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": _build_user_prompt(parsed)},
    ]

    for turn in range(MAX_AGENT_TURNS):
        logger.info("Resource agent — turn %d", turn + 1)

        # Rate-limit pause (Groq free tier: 30 req/min)
        if turn > 0:
            time.sleep(3)

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            temperature=0.3,
        )

        choice = response.choices[0]
        assistant_msg = choice.message

        # Append the assistant's reply (may contain tool_calls)
        messages.append(assistant_msg.model_dump())

        # If no tool calls, the model decided to stop — try to parse content
        if not assistant_msg.tool_calls:
            logger.info("Agent stopped without calling finish(); extracting from content")
            break

        # Process each tool call
        finish_result: str | None = None
        for tc in assistant_msg.tool_calls:
            fn_name = tc.function.name
            try:
                fn_args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                fn_args = {}

            logger.info("  Tool call: %s(%s)", fn_name, list(fn_args.keys()))
            result = _execute_tool_call(fn_name, fn_args)

            # Append tool result so the agent can see it next turn
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

            if fn_name == "finish":
                finish_result = result

        # If the agent called finish(), we're done
        if finish_result is not None:
            logger.info("Agent called finish() — parsing recommendations")
            return _parse_recommendations(finish_result, parsed.course_name)

    # Fallback: try to extract recommendations from the last assistant message
    logger.warning("Agent exhausted %d turns without calling finish()", MAX_AGENT_TURNS)
    last_content = ""
    for msg in reversed(messages):
        if isinstance(msg, dict):
            content = msg.get("content", "")
        else:
            content = getattr(msg, "content", "") or ""
        if content and "topic_resources" in content:
            last_content = content
            break

    if last_content:
        return _parse_recommendations(last_content, parsed.course_name)

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
        # Try to extract JSON from markdown code fence
        import re
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
