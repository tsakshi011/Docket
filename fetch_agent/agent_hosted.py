"""Docket Study-Resource Agent — Agentverse Hosted Version.

Paste this code into the Agentverse Agent Editor (Build tab).
Add these secrets in the Agentverse Secrets tab:
  - GROQ_API_KEY   (from https://console.groq.com/keys)
  - TAVILY_API_KEY  (from https://tavily.com)
"""

import json
import requests
from datetime import datetime
from uuid import uuid4

from openai import OpenAI
from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
GROQ_MODEL = "llama-3.1-8b-instant"
MAX_TURNS = 4

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

# ---------------------------------------------------------------------------
# Tavily search via REST API (tavily package not available on Agentverse)
# ---------------------------------------------------------------------------
TAVILY_API_URL = "https://api.tavily.com/search"

DOMAIN_MAP = {
    "search_youtube": ["youtube.com", "youtu.be"],
    "search_academic": [
        "ocw.mit.edu", "openstax.org", "coursera.org",
        "edx.org", "khanacademy.org", "scholar.google.com",
    ],
    "search_practice": [
        "leetcode.com", "khanacademy.org", "brilliant.org",
        "geeksforgeeks.org", "hackerrank.com", "quizlet.com",
    ],
    "search_web": [],
}


def tavily_search(query: str, tavily_key: str, tool_name: str = "search_web") -> str:
    """Call Tavily REST API directly."""
    try:
        payload = {
            "api_key": tavily_key,
            "query": query,
            "max_results": 3,
            "include_domains": DOMAIN_MAP.get(tool_name, []),
        }
        resp = requests.post(TAVILY_API_URL, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        results = [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", "")[:200],
            }
            for r in data.get("results", [])
        ]
        return json.dumps(results)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# ReAct resource search loop
# ---------------------------------------------------------------------------
def extract_json(text: str) -> dict | None:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    import re
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return None


def run_resource_search(user_query: str, groq_key: str, tavily_key: str) -> str:
    """Run the ReAct tool-calling loop and return formatted results."""
    client = OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query},
    ]

    for turn in range(MAX_TURNS):
        try:
            resp = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.3,
            )
        except Exception as e:
            return f"Sorry, I hit an API error. Please try again shortly. ({e})"

        content = resp.choices[0].message.content or ""
        messages.append({"role": "assistant", "content": content})

        parsed = extract_json(content)
        if parsed is None:
            messages.append({
                "role": "user",
                "content": "Respond with valid JSON containing 'action' and 'action_input'.",
            })
            continue

        action = parsed.get("action", "")
        action_input = parsed.get("action_input", {})

        if action == "finish":
            return format_results(action_input if isinstance(action_input, dict) else {})

        if isinstance(action_input, str):
            action_input = {"query": action_input}

        if action not in DOMAIN_MAP:
            messages.append({
                "role": "user",
                "content": f"Unknown tool '{action}'. Use: search_web, search_youtube, search_academic, search_practice, finish.",
            })
            continue

        query = action_input.get("query", "")
        observation = tavily_search(query, tavily_key, action)
        if len(observation) > 1500:
            observation = observation[:1500] + "..."

        messages.append({"role": "user", "content": f"Result({action}):\n{observation}"})

        # Sliding window: keep system + user prompt + last 3 pairs
        if len(messages) > 8:
            messages = messages[:2] + messages[-6:]

    return "I wasn't able to find enough resources in time. Please try a more specific course name."


def format_results(data: dict) -> str:
    """Format JSON recommendations into readable text."""
    lines = []
    course = data.get("course_name", "your course")
    lines.append(f"Here are the best study resources I found for **{course}**:\n")

    for r in data.get("general_resources", []):
        title = r.get("title", "Untitled")
        url = r.get("url", "")
        platform = r.get("platform", "")
        rtype = r.get("resource_type", "")
        relevance = r.get("relevance", "")
        link = f"[{title}]({url})" if url else title
        lines.append(f"- {link} ({platform}, {rtype}) — {relevance}")

    for t in data.get("topic_resources", []):
        lines.append(f"\n**{t.get('topic', 'Topic')}:**")
        for r in t.get("resources", []):
            title = r.get("title", "Untitled")
            url = r.get("url", "")
            platform = r.get("platform", "")
            rtype = r.get("resource_type", "")
            link = f"[{title}]({url})" if url else title
            lines.append(f"- {link} ({platform}, {rtype})")

    tips = data.get("study_tips", [])
    if tips:
        lines.append("\n**Study Tips:**")
        for tip in tips:
            lines.append(f"- {tip}")

    return "\n".join(lines) if lines else "No resources found. Try rephrasing your query."


# ---------------------------------------------------------------------------
# Fetch.ai Agent + Chat Protocol
# ---------------------------------------------------------------------------
agent = Agent()
protocol = Protocol(spec=chat_protocol_spec)


def create_text_chat(text: str, end_session: bool = True) -> ChatMessage:
    content = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent(type="end-session"))
    return ChatMessage(timestamp=datetime.utcnow(), msg_id=uuid4(), content=content)


@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id),
    )

    # Extract user text
    user_text = ""
    for item in msg.content:
        if isinstance(item, TextContent):
            user_text += item.text

    if not user_text.strip():
        await ctx.send(sender, create_text_chat(
            "Hi! I'm the Docket Study Resource Agent. "
            "Tell me a course name (e.g., 'Organic Chemistry' or "
            "'CS 161 Data Structures') and I'll find the best free "
            "study resources for you!"
        ))
        return

    # Get API keys from Agentverse secrets
    groq_key = ctx.get_secret("GROQ_API_KEY")
    tavily_key = ctx.get_secret("TAVILY_API_KEY")

    if not groq_key or not tavily_key:
        await ctx.send(sender, create_text_chat(
            "Configuration error: GROQ_API_KEY and TAVILY_API_KEY must be set "
            "in the agent's Secrets tab on Agentverse."
        ))
        return

    ctx.logger.info(f"Searching resources for: {user_text[:100]}")
    response_text = run_resource_search(user_text, groq_key, tavily_key)
    await ctx.send(sender, create_text_chat(response_text))


@protocol.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


agent.include(protocol, publish_manifest=True)
