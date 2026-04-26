"""Tools that the resource-routing agent can call autonomously.

Each public function here is registered as a tool the LLM can invoke via
Groq's function-calling API.  The functions do the actual I/O (web search,
etc.) and return plain-text observations the agent uses for its next
reasoning step.

Design notes
------------
* DuckDuckGo search is free and keyless — perfect for a hackathon MVP.
* Every tool returns a *string* (the "observation") so the agent loop stays
  simple: Thought → Action → Observation → Thought …
* We cap results to keep token usage low on the small 8B model.
"""

from __future__ import annotations

import json
import logging
import urllib.parse
from typing import Any

from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool: general web search
# ---------------------------------------------------------------------------

def search_web(query: str, max_results: int = 5) -> str:
    """Search the web for educational resources.

    Returns a JSON list of {title, url, snippet} objects.
    """
    try:
        with DDGS() as ddgs:
            hits = list(ddgs.text(query, max_results=max_results))
        results = [
            {"title": h["title"], "url": h["href"], "snippet": h["body"]}
            for h in hits
        ]
        return json.dumps(results, indent=2)
    except Exception as exc:
        logger.warning("search_web failed: %s", exc)
        return json.dumps({"error": str(exc)})


# ---------------------------------------------------------------------------
# Tool: YouTube video search
# ---------------------------------------------------------------------------

def search_youtube(query: str, max_results: int = 5) -> str:
    """Search YouTube for educational videos on a topic.

    Uses DuckDuckGo scoped to site:youtube.com so no API key is needed.
    Returns a JSON list of {title, url, snippet}.
    """
    scoped = f"site:youtube.com {query}"
    try:
        with DDGS() as ddgs:
            hits = list(ddgs.text(scoped, max_results=max_results))
        results = [
            {"title": h["title"], "url": h["href"], "snippet": h["body"]}
            for h in hits
        ]
        return json.dumps(results, indent=2)
    except Exception as exc:
        logger.warning("search_youtube failed: %s", exc)
        return json.dumps({"error": str(exc)})


# ---------------------------------------------------------------------------
# Tool: academic / textbook search
# ---------------------------------------------------------------------------

def search_academic(query: str, max_results: int = 5) -> str:
    """Search for academic textbooks, papers, and course materials.

    Scoped to educational domains (MIT OCW, OpenStax, Google Scholar, etc.).
    """
    scoped = (
        f"{query} "
        "(site:ocw.mit.edu OR site:openstax.org OR site:scholar.google.com "
        "OR site:coursera.org OR site:edx.org OR site:khanacademy.org)"
    )
    try:
        with DDGS() as ddgs:
            hits = list(ddgs.text(scoped, max_results=max_results))
        results = [
            {"title": h["title"], "url": h["href"], "snippet": h["body"]}
            for h in hits
        ]
        return json.dumps(results, indent=2)
    except Exception as exc:
        logger.warning("search_academic failed: %s", exc)
        return json.dumps({"error": str(exc)})


# ---------------------------------------------------------------------------
# Tool: practice problem search
# ---------------------------------------------------------------------------

def search_practice(query: str, max_results: int = 5) -> str:
    """Search for practice problems, exercises, and problem sets.

    Scoped to sites known for practice content.
    """
    scoped = (
        f"{query} practice problems exercises "
        "(site:leetcode.com OR site:khanacademy.org OR site:brilliant.org "
        "OR site:geeksforgeeks.org OR site:hackerrank.com OR site:quizlet.com)"
    )
    try:
        with DDGS() as ddgs:
            hits = list(ddgs.text(scoped, max_results=max_results))
        results = [
            {"title": h["title"], "url": h["href"], "snippet": h["body"]}
            for h in hits
        ]
        return json.dumps(results, indent=2)
    except Exception as exc:
        logger.warning("search_practice failed: %s", exc)
        return json.dumps({"error": str(exc)})


# ---------------------------------------------------------------------------
# Tool: finish — agent calls this to submit final recommendations
# ---------------------------------------------------------------------------

def finish(recommendations_json: str) -> str:
    """Signal that resource collection is complete.

    The agent calls this with a JSON string containing the final
    ResourceRecommendations payload.  We just pass it through — the
    agent loop checks for this tool name to break out.
    """
    return recommendations_json


# ---------------------------------------------------------------------------
# OpenAI-compatible tool definitions for Groq function calling
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": (
                "Search the web for educational resources on a topic. "
                "Returns a JSON list of {title, url, snippet}."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for finding study resources",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_youtube",
            "description": (
                "Search YouTube for educational videos and lectures. "
                "Returns a JSON list of {title, url, snippet}."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for finding YouTube videos",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_academic",
            "description": (
                "Search academic platforms (MIT OCW, OpenStax, Coursera, Khan Academy, edX) "
                "for textbooks, courses, and lecture materials. "
                "Returns a JSON list of {title, url, snippet}."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for academic resources",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_practice",
            "description": (
                "Search for practice problems, exercises, quizzes on platforms like "
                "LeetCode, Khan Academy, Brilliant, GeeksforGeeks, HackerRank, Quizlet. "
                "Returns a JSON list of {title, url, snippet}."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for practice problems",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finish",
            "description": (
                "Call this when you have collected enough resources for every topic. "
                "Pass the final recommendations as a JSON string matching the "
                "ResourceRecommendations schema."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "recommendations_json": {
                        "type": "string",
                        "description": (
                            "JSON string with keys: course_name, subject_domain, "
                            "general_resources (list of {title, url, resource_type, "
                            "platform, relevance, priority}), topic_resources (list of "
                            "{topic, related_events, resources}), study_tips (list of strings)"
                        ),
                    },
                },
                "required": ["recommendations_json"],
            },
        },
    },
]

# Map tool names → Python callables
TOOL_DISPATCH: dict[str, Any] = {
    "search_web": search_web,
    "search_youtube": search_youtube,
    "search_academic": search_academic,
    "search_practice": search_practice,
    "finish": finish,
}
