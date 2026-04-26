import json
import logging
import os
import time

from openai import APIStatusError, OpenAI, RateLimitError

from app.models.schemas import ParsedSyllabus, StudyPlan
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
#GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_MODEL = "llama-3.1-8b-instant"

# Reserve tokens for system prompt (~600) and response (~3,000).
#MAX_USER_TOKENS = 6_000
# The 8B fallback model has a 6 000 TPM cap; keep user text well under that.
MAX_USER_TOKENS = 1_500
CHARS_PER_TOKEN_ESTIMATE = 4

def _extract_system_prompt() -> str:
    from datetime import date as _date

    today = _date.today()
    current_year = today.year
    # Academic year: Fall uses current year, Spring uses next year
    next_year = current_year + 1

    return f"""You are an expert academic syllabus parser. Given the raw text of a course syllabus, extract ALL important dates and deadlines.

IMPORTANT — Today's date is {today.isoformat()}.
When the syllabus does NOT explicitly state a year, use these rules:
- Fall semester dates (August–December) → use {current_year}
- Spring semester dates (January–May) → use {next_year}
- Summer semester dates (June–July) → use {next_year}
If the syllabus DOES state a year, use that year.

For each event provide:
- title: descriptive name (e.g., "Midterm Exam", "HW3 Due", "Final Project Proposal Due")
- date: ISO 8601 date string (YYYY-MM-DD)
- time: start time if mentioned (HH:MM in 24h format), or null
- duration_minutes: estimated duration (120 for exams, 60 for quizzes, 30 for assignment submissions)
- event_type: one of "exam", "assignment", "quiz", "reading", "lecture", "lab", "project", "other"
- description: any additional context (room, chapter, instructions, format)
- weight: grade weight if mentioned (e.g., "20% of final grade")

Be thorough. Include assignment due dates, exam dates, project milestones, quiz dates, reading deadlines, and any other scheduled academic items. Resolve relative dates like "Week 5" using the semester start date.

You MUST respond with valid JSON matching this exact schema:
{{
  "course_name": "string",
  "semester": "string",
  "instructor": "string or null",
  "events": [
    {{
      "title": "string",
      "date": "YYYY-MM-DD",
      "time": "HH:MM or null",
      "duration_minutes": number,
      "event_type": "exam|assignment|quiz|reading|lecture|lab|project|other",
      "description": "string",
      "weight": "string or null"
    }}
  ]
}}"""

STUDY_PLAN_SYSTEM_PROMPT = """You are an expert academic study planner and time management coach. Given a list of syllabus events (assignments, exams, projects), generate an optimal study plan.

Your job is to REASON about how to break down each assignment and exam into manageable preparation steps, then schedule them optimally.

Rules for generating study blocks:
1. **Assignments**: Break into sub-tasks. A research paper gets: "Choose topic", "Research & gather sources", "Write outline", "Write first draft", "Revise & edit", "Final review". Space these evenly before the due date.
2. **Exams**: Create review sessions. A midterm gets 3-5 study sessions in the week before. A final gets 5-7 sessions over 2 weeks. Include "Review notes", "Practice problems", "Study group prep".
3. **Projects**: Break into milestones even if the syllabus doesn't. "Project due Dec 10" → "Project planning" (3 weeks before), "Implementation" (2 weeks before), "Testing" (1 week before), "Polish & submit" (2 days before).
4. **Quizzes**: Add 1-2 review sessions in the 2 days before each quiz.
5. **Readings**: Schedule reading time at least 2 days before the class where it's discussed.
6. **Load balancing**: Don't cluster too many study blocks on one day. Spread them out. Max 3 study blocks per day.
7. **Priority**: Assign "critical" to exam prep and final projects, "high" to major assignments, "medium" to regular homework, "low" to readings.
8. **Warnings**: Flag heavy weeks where multiple deadlines cluster. Flag if two exams are within 2 days of each other.

You MUST respond with valid JSON matching this exact schema:
{
  "course_name": "string",
  "semester": "string",
  "syllabus_events": [],
  "study_blocks": [
    {
      "title": "string (e.g., 'Study: Review Ch. 5-7 for Midterm')",
      "date": "YYYY-MM-DD",
      "time": "HH:MM or null",
      "duration_minutes": number (45-120),
      "block_type": "study_session|draft_deadline|outline|review|practice|break_down|research|writing|revision",
      "related_event": "string (title of parent assignment/exam)",
      "description": "string (specific instructions)",
      "priority": "low|medium|high|critical"
    }
  ],
  "weekly_summary": ["string (one-line summary per week)"],
  "warnings": ["string (alerts about heavy weeks, conflicts)"]
}"""


def _get_client() -> OpenAI:
    api_key = os.environ["GROQ_API_KEY"]
    return OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)


def _is_rate_or_size_error(exc: Exception) -> bool:
    """Return True for 429 rate-limit or 413 request-too-large errors."""
    if isinstance(exc, RateLimitError):
        return True
    if isinstance(exc, APIStatusError) and exc.status_code == 413:
        return True
    return False


def _estimate_tokens(text: str) -> int:
    return len(text) // CHARS_PER_TOKEN_ESTIMATE


def _chunk_text(text: str, max_tokens: int = MAX_USER_TOKENS) -> list[str]:
    """Split text into chunks that each fit within the token budget.

    Splits on paragraph boundaries (double-newline) first, then falls back to
    single newlines so that context within a paragraph is kept together.
    """
    max_chars = max_tokens * CHARS_PER_TOKEN_ESTIMATE

    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    current_chunk: list[str] = []
    current_len = 0

    paragraphs = text.split("\n\n")
    for para in paragraphs:
        para_with_sep = para + "\n\n"
        if current_len + len(para_with_sep) > max_chars and current_chunk:
            chunks.append("".join(current_chunk).rstrip())
            current_chunk = []
            current_len = 0

        if len(para_with_sep) > max_chars:
            # paragraph itself is too large – split on single newlines
            for line in para.split("\n"):
                line_with_sep = line + "\n"
                if current_len + len(line_with_sep) > max_chars and current_chunk:
                    chunks.append("".join(current_chunk).rstrip())
                    current_chunk = []
                    current_len = 0
                current_chunk.append(line_with_sep)
                current_len += len(line_with_sep)
        else:
            current_chunk.append(para_with_sep)
            current_len += len(para_with_sep)

    if current_chunk:
        chunks.append("".join(current_chunk).rstrip())

    return chunks


def _sanitize_events(events: list[dict]) -> list[dict]:
    """Drop events that are missing required fields the LLM sometimes omits."""
    cleaned: list[dict] = []
    for ev in events:
        if not isinstance(ev, dict):
            continue
        if not ev.get("title") or not ev.get("date"):
            continue
        if ev.get("duration_minutes") is None:
            ev.pop("duration_minutes", None)
        cleaned.append(ev)
    return cleaned


def _extract_events_single(
    client: OpenAI, text: str, model: str = GROQ_MODEL,
) -> dict:
    """Send a single chunk to Groq and return the raw parsed dict."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _extract_system_prompt()},
            {"role": "user", "content": text},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    return json.loads(response.choices[0].message.content)


def _extract_events_with_model(
    client: OpenAI,
    syllabus_text: str,
    model: str,
    max_user_tokens: int,
) -> ParsedSyllabus:
    """Run extraction with a specific model and token budget."""
    chunks = _chunk_text(syllabus_text, max_tokens=max_user_tokens)

    if len(chunks) == 1:
        raw = _extract_events_single(client, chunks[0], model=model)
        raw["events"] = _sanitize_events(raw.get("events", []))
        return ParsedSyllabus(**raw)

    all_events: list[dict] = []
    course_name = ""
    semester = ""
    instructor = None

    for i, chunk in enumerate(chunks):
        if i > 0:
            time.sleep(15)
        raw = _extract_events_single(client, chunk, model=model)
        if not course_name:
            course_name = raw.get("course_name", "")
            semester = raw.get("semester", "")
            instructor = raw.get("instructor")
        all_events.extend(_sanitize_events(raw.get("events", [])))

    seen: set[tuple[str, str]] = set()
    unique_events: list[dict] = []
    for ev in all_events:
        key = (ev.get("title", ""), ev.get("date", ""))
        if key not in seen:
            seen.add(key)
            unique_events.append(ev)

    return ParsedSyllabus(
        course_name=course_name,
        semester=semester,
        instructor=instructor,
        events=unique_events,
    )


def extract_events(syllabus_text: str) -> ParsedSyllabus:
    """Step 1: Extract raw events from syllabus text.

    Tries the primary model first.  On rate-limit / request-too-large errors
    it retries with the smaller fallback model and tighter chunk sizes.
    """
    client = _get_client()
    
    return _extract_events_with_model(
        client, syllabus_text, GROQ_MODEL, MAX_USER_TOKENS,
    )
    '''except (RateLimitError, APIStatusError) as exc:
        if not _is_rate_or_size_error(exc):
            raise
        logger.warning(
            "Primary model unavailable (%s), falling back to %s",
            exc, GROQ_FALLBACK_MODEL,
        )
        return _extract_events_with_model(
            client, syllabus_text, GROQ_FALLBACK_MODEL, FALLBACK_MAX_USER_TOKENS,
        )'''


def generate_study_plan(parsed: ParsedSyllabus) -> StudyPlan:
    """Step 2: Generate an autonomous study plan based on extracted events."""
    client = _get_client()

    events_summary = "\n".join(
        f"- {e.title} ({e.event_type}) — {e.date}"
        + (f" at {e.time}" if e.time else "")
        + (f" — Weight: {e.weight}" if e.weight else "")
        + (f" — {e.description}" if e.description else "")
        for e in parsed.events
    )

    user_prompt = f"""Course: {parsed.course_name}
Semester: {parsed.semester}

Syllabus events:
{events_summary}

Generate an optimal study plan with preparation blocks for each event. Break down large assignments into sub-tasks. Schedule study sessions before exams. Balance the workload across weeks."""

    messages = [
        {"role": "system", "content": STUDY_PLAN_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    '''except (RateLimitError, APIStatusError) as exc:
        if not _is_rate_or_size_error(exc):
            raise
        logger.warning(
            "Primary model unavailable (%s), falling back to %s",
            exc, GROQ_FALLBACK_MODEL,
        )
        response = client.chat.completions.create(
            model=GROQ_FALLBACK_MODEL,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.1,
        )'''

    raw = json.loads(response.choices[0].message.content)
    raw.setdefault("weekly_summary", [])
    raw.setdefault("warnings", [])
    raw.setdefault("syllabus_events", [])

    for block in raw.get("study_blocks", []):
        if isinstance(block, dict) and block.get("duration_minutes") is None:
            block.pop("duration_minutes", None)

    raw["syllabus_events"] = []
    return StudyPlan(**raw)


def run_agent_pipeline(syllabus_text: str) -> StudyPlan:
    """Full agentic pipeline: Extract → Reason → Plan."""
    # Step 1: Extract events from syllabus
    parsed = extract_events(syllabus_text)

    # Pause between pipeline steps Groq's TPM rate limit.
    time.sleep(15)

    # Step 2: Generate autonomous study plan
    plan = generate_study_plan(parsed)

    # Ensure the original syllabus events are included
    plan.syllabus_events = parsed.events

    return plan
