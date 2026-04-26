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

from openai import OpenAI, RateLimitError

from app.models.schemas import (
    ParsedSyllabus,
    ResourceRecommendations,
    StudyPlan,
)
from app.services.resource_tools import TOOL_DISPATCH

logger = logging.getLogger(__name__)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "llama-3.1-8b-instant"  # default: cheap, fast, separate TPD quota
GROQ_FALLBACK_MODEL = "llama-3.3-70b-versatile"  # fallback: higher quality
MAX_AGENT_TURNS = 5  # safety cap so we don't loop forever
_BASE_DELAY = 2  # seconds between agent turns (Groq free tier: 30 req/min)
_MAX_RETRIES = 2  # retries per LLM call on rate-limit errors
_MAX_OBSERVATION_CHARS = 1500  # truncate tool results to save tokens
_CONTEXT_WINDOW = 3  # keep only this many recent tool observations

RESOURCE_AGENT_SYSTEM_PROMPT = """\
You are a study-resource curator. Search the web and return the best FREE
resources for a university course.

Tools: search_web, search_youtube, search_academic, search_practice.

Rules:
- Make at most 3-4 tool calls total, then finish.
- ONE search_youtube for the whole course; ONE tool per key topic.
- Use REAL URLs from search results only.
- Respond with a JSON object every turn. No markdown.

Tool call: {"thought":"...","action":"<tool>","action_input":{"query":"..."}}
Finish:    {"thought":"done","action":"finish","action_input":<RESULT>}

RESULT schema:
{"course_name":"str","subject_domain":"str",
 "general_resources":[{"title":"str","url":"str|null","resource_type":"video|textbook|practice|article|tool|course","platform":"str","relevance":"str","priority":"high|medium|low"}],
 "topic_resources":[{"topic":"str","related_events":["str"],"resources":[...same...]}],
 "study_tips":["str"]}
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


def _is_daily_limit(exc: RateLimitError) -> bool:
    """Return True if the error is a daily token quota (TPD) exhaustion."""
    msg = str(exc).lower()
    return "tokens per day" in msg or "(tpd)" in msg


def _llm_call_with_retry(client: OpenAI, model: str, messages: list[dict]):
    """Call the Groq chat API with exponential backoff on 429 errors.

    If the error is a daily token limit (TPD), returns ``None`` immediately
    so the caller can switch to the fallback model without wasting time.
    Only retries on per-minute / per-second rate limits.
    """
    for attempt in range(_MAX_RETRIES):
        try:
            return client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.3,
            )
        except RateLimitError as exc:
            if _is_daily_limit(exc):
                logger.warning(
                    "Daily token limit (TPD) hit on %s — skipping retries",
                    model,
                )
                return None
            wait = _BASE_DELAY * (2 ** attempt)
            logger.warning(
                "Rate-limited (attempt %d/%d) on %s — waiting %ds: %s",
                attempt + 1, _MAX_RETRIES, model, wait, exc,
            )
            if attempt < _MAX_RETRIES - 1:
                time.sleep(wait)
        except Exception as exc:
            logger.error("Groq API error on %s: %s", model, exc)
            return None
    return None


def _trim_context(messages: list[dict]) -> None:
    """Keep only the system prompt, initial user prompt, and the last
    ``_CONTEXT_WINDOW`` assistant+user turn pairs.  Edits *in place*."""
    prefix = 2  # system + initial user prompt
    tail = messages[prefix:]
    max_tail = _CONTEXT_WINDOW * 2  # each turn = assistant + user
    if len(tail) > max_tail:
        messages[prefix:] = tail[-max_tail:]


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

        # Rate-limit pause (Groq free tier: ~30 req/min)
        if turn > 0:
            time.sleep(_BASE_DELAY)

        response = _llm_call_with_retry(client, model, messages)
        if response is None and model == GROQ_MODEL:
            logger.warning("Primary model rate-limited — switching to fallback")
            model = GROQ_FALLBACK_MODEL
            time.sleep(_BASE_DELAY)
            response = _llm_call_with_retry(client, model, messages)
        if response is None:
            logger.error("All models rate-limited after retries")
            break

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
        if len(observation) > _MAX_OBSERVATION_CHARS:
            observation = observation[:_MAX_OBSERVATION_CHARS] + "…"

        messages.append({
            "role": "user",
            "content": f"Result({action}):\n{observation}",
        })

        # Sliding window: drop old tool observations to keep context small.
        # Keep system + initial user prompt (first 2 msgs) and the most
        # recent _CONTEXT_WINDOW pairs of (assistant, user/tool-result).
        _trim_context(messages)

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
        study_tips=[
            "The AI resource search hit a rate limit. "
            "Your daily Groq token quota may be exhausted — "
            "try again in a few hours or upgrade at https://console.groq.com/settings/billing",
        ],
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
