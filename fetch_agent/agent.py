"""Docket Study-Resource Agent for Fetch.ai Agentverse / ASI:One.

This agent is discoverable via ASI:One and responds to natural-language
queries about university courses by searching the web for the best free
study resources (videos, textbooks, practice problems, articles).

It implements the mandatory **Chat Protocol** so ASI:One can route
messages to it, and wraps Docket's existing ReAct resource-search
pipeline (Tavily web search + Groq LLM).

Usage
-----
    export GROQ_API_KEY="..."
    export TAVILY_API_KEY="..."
    export AGENT_SEED="<your-unique-seed-phrase>"
    python fetch_agent/agent.py
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from uuid import uuid4

from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

# ---------------------------------------------------------------------------
# Make Docket's backend importable
# ---------------------------------------------------------------------------
_BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "backend")
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, os.path.abspath(_BACKEND_DIR))

from app.services.resource_tools import TOOL_DISPATCH  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("docket-fetch-agent")

# ---------------------------------------------------------------------------
# Groq LLM helper (lightweight, no full agent loop dependency)
# ---------------------------------------------------------------------------
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
MAX_TURNS = 4
_DELAY = 6

SYSTEM_PROMPT = """\
You are Docket, a study-resource curator. Given a university course name
(and optionally topics), search the web and return the best FREE resources.

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
 "topic_resources":[{"topic":"str","resources":[...same...]}],
 "study_tips":["str"]}
"""


def _get_groq_client():
    from openai import OpenAI

    return OpenAI(
        api_key=os.environ["GROQ_API_KEY"],
        base_url=GROQ_BASE_URL,
    )


def _extract_json(text: str) -> dict | None:
    import re

    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return None


def run_resource_search(user_query: str) -> str:
    """Run the ReAct tool-calling loop and return a formatted text response."""
    client = _get_groq_client()
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query},
    ]

    for turn in range(MAX_TURNS):
        if turn > 0:
            time.sleep(_DELAY)
        try:
            resp = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.3,
            )
        except Exception as exc:
            logger.error("Groq API error: %s", exc)
            return f"Sorry, I hit a rate limit or API error. Please try again shortly. ({exc})"

        content = resp.choices[0].message.content or ""
        messages.append({"role": "assistant", "content": content})

        parsed = _extract_json(content)
        if parsed is None:
            messages.append({
                "role": "user",
                "content": "Respond with valid JSON containing 'action' and 'action_input'.",
            })
            continue

        action = parsed.get("action", "")
        action_input = parsed.get("action_input", {})

        if action == "finish":
            return _format_results(action_input if isinstance(action_input, dict) else {})

        if isinstance(action_input, str):
            action_input = {"query": action_input}

        tool_fn = TOOL_DISPATCH.get(action)
        if tool_fn is None:
            messages.append({"role": "user", "content": f"Unknown tool '{action}'. Use one of: search_web, search_youtube, search_academic, search_practice, finish."})
            continue

        query = action_input.get("query", "")
        logger.info("Tool call: %s(%s)", action, query[:80])
        observation = tool_fn(query)
        if len(observation) > 1500:
            observation = observation[:1500] + "..."

        messages.append({"role": "user", "content": f"Result({action}):\n{observation}"})

    return "I wasn't able to find enough resources in time. Please try a more specific course name."


def _format_results(data: dict) -> str:
    """Format the JSON recommendations into a readable text response."""
    lines: list[str] = []
    course = data.get("course_name", "your course")
    lines.append(f"Here are the best study resources I found for **{course}**:\n")

    general = data.get("general_resources", [])
    if general:
        lines.append("**General Resources:**")
        for r in general:
            title = r.get("title", "Untitled")
            url = r.get("url", "")
            platform = r.get("platform", "")
            rtype = r.get("resource_type", "")
            relevance = r.get("relevance", "")
            link = f"[{title}]({url})" if url else title
            lines.append(f"- {link} ({platform}, {rtype}) - {relevance}")
        lines.append("")

    topics = data.get("topic_resources", [])
    for t in topics:
        topic_name = t.get("topic", "Topic")
        lines.append(f"**{topic_name}:**")
        for r in t.get("resources", []):
            title = r.get("title", "Untitled")
            url = r.get("url", "")
            platform = r.get("platform", "")
            rtype = r.get("resource_type", "")
            link = f"[{title}]({url})" if url else title
            lines.append(f"- {link} ({platform}, {rtype})")
        lines.append("")

    tips = data.get("study_tips", [])
    if tips:
        lines.append("**Study Tips:**")
        for tip in tips:
            lines.append(f"- {tip}")

    return "\n".join(lines) if lines else "No resources found. Try rephrasing your query."


# ---------------------------------------------------------------------------
# Fetch.ai Agent setup
# ---------------------------------------------------------------------------
AGENT_SEED = os.getenv("AGENT_SEED", "docket-study-resource-agent-default-seed")
AGENT_PORT = int(os.getenv("AGENT_PORT", "8001"))

agent = Agent(
    name="docket-study-resources",
    seed=AGENT_SEED,
    port=AGENT_PORT,
    mailbox=True,
    publish_agent_details=True,
)

protocol = Protocol(spec=chat_protocol_spec)


@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(
        sender,
        ChatAcknowledgement(
            timestamp=datetime.now(timezone.utc),
            acknowledged_msg_id=msg.msg_id,
        ),
    )

    # Collect user text
    user_text = ""
    for item in msg.content:
        if isinstance(item, TextContent):
            user_text += item.text

    if not user_text.strip():
        response_text = (
            "Hi! I'm the Docket Study Resource Agent. "
            "Tell me a course name (e.g., 'Organic Chemistry' or "
            "'CS 161 Data Structures') and I'll find the best free "
            "study resources for you!"
        )
    else:
        ctx.logger.info("Searching resources for: %s", user_text[:100])
        response_text = run_resource_search(user_text)

    await ctx.send(
        sender,
        ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[
                TextContent(type="text", text=response_text),
                EndSessionContent(type="end-session"),
            ],
        ),
    )


@protocol.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


agent.include(protocol, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
