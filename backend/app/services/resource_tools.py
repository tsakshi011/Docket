"""Tools that the resource-routing agent can call autonomously.

Each public function here is registered as a tool the LLM can invoke.
The functions do the actual I/O (web search via Tavily) and return
plain-text observations the agent uses for its next reasoning step.

Design notes
------------
* Tavily is purpose-built for AI agents — returns clean, structured results
  with no CAPTCHA issues.  Free tier: 1 000 searches / month.
* Every tool returns a *string* (the "observation") so the agent loop stays
  simple: Thought → Action → Observation → Thought …
* We cap results to keep token usage low.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from tavily import TavilyClient

logger = logging.getLogger(__name__)


def _get_tavily() -> TavilyClient:
    api_key = os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "TAVILY_API_KEY is not set. Get a free key at https://tavily.com"
        )
    return TavilyClient(api_key=api_key)


def _tavily_search(
    query: str,
    *,
    max_results: int = 3,
    include_domains: list[str] | None = None,
) -> str:
    """Run a Tavily search and return compact JSON results."""
    try:
        client = _get_tavily()
        response = client.search(
            query=query,
            max_results=max_results,
            include_domains=include_domains or [],
        )
        results = [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", "")[:200],
            }
            for r in response.get("results", [])
        ]
        return json.dumps(results)
    except Exception as exc:
        logger.warning("Tavily search failed: %s", exc)
        return json.dumps({"error": str(exc)})


# ---------------------------------------------------------------------------
# Tool: general web search
# ---------------------------------------------------------------------------

def search_web(query: str, max_results: int = 3) -> str:
    """Search the web for educational resources.

    Returns a JSON list of {title, url, snippet} objects.
    """
    return _tavily_search(query, max_results=max_results)


# ---------------------------------------------------------------------------
# Tool: YouTube video search
# ---------------------------------------------------------------------------

def search_youtube(query: str, max_results: int = 3) -> str:
    """Search YouTube for educational videos on a topic.

    Returns a JSON list of {title, url, snippet}.
    """
    return _tavily_search(
        query,
        max_results=max_results,
        include_domains=["youtube.com", "youtu.be"],
    )


# ---------------------------------------------------------------------------
# Tool: academic / textbook search
# ---------------------------------------------------------------------------

def search_academic(query: str, max_results: int = 3) -> str:
    """Search for academic textbooks, papers, and course materials.

    Scoped to educational domains (MIT OCW, OpenStax, Coursera, etc.).
    """
    return _tavily_search(
        query,
        max_results=max_results,
        include_domains=[
            "ocw.mit.edu",
            "openstax.org",
            "coursera.org",
            "edx.org",
            "khanacademy.org",
            "scholar.google.com",
        ],
    )


# ---------------------------------------------------------------------------
# Tool: practice problem search
# ---------------------------------------------------------------------------

def search_practice(query: str, max_results: int = 3) -> str:
    """Search for practice problems, exercises, and problem sets.

    Scoped to sites known for practice content.
    """
    return _tavily_search(
        f"{query} practice problems",
        max_results=max_results,
        include_domains=[
            "leetcode.com",
            "khanacademy.org",
            "brilliant.org",
            "geeksforgeeks.org",
            "hackerrank.com",
            "quizlet.com",
        ],
    )


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
