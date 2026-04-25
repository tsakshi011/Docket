import json
import os

from openai import OpenAI

from app.models.schemas import ParsedSyllabus, StudyPlan

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "llama-3.3-70b-versatile"

EXTRACT_SYSTEM_PROMPT = """You are an expert academic syllabus parser. Given the raw text of a course syllabus, extract ALL important dates and deadlines.

For each event provide:
- title: descriptive name (e.g., "Midterm Exam", "HW3 Due", "Final Project Proposal Due")
- date: ISO 8601 date string (YYYY-MM-DD). Infer the year from the semester/term context.
- time: start time if mentioned (HH:MM in 24h format), or null
- duration_minutes: estimated duration (120 for exams, 60 for quizzes, 30 for assignment submissions)
- event_type: one of "exam", "assignment", "quiz", "reading", "lecture", "lab", "project", "other"
- description: any additional context (room, chapter, instructions, format)
- weight: grade weight if mentioned (e.g., "20% of final grade")

Be thorough. Include assignment due dates, exam dates, project milestones, quiz dates, reading deadlines, and any other scheduled academic items. Resolve relative dates like "Week 5" using the semester start date.

You MUST respond with valid JSON matching this exact schema:
{
  "course_name": "string",
  "semester": "string",
  "instructor": "string or null",
  "events": [
    {
      "title": "string",
      "date": "YYYY-MM-DD",
      "time": "HH:MM or null",
      "duration_minutes": number,
      "event_type": "exam|assignment|quiz|reading|lecture|lab|project|other",
      "description": "string",
      "weight": "string or null"
    }
  ]
}"""

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
    api_key = os.environ.get("GROQ_API_KEY", "")
    return OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)


def extract_events(syllabus_text: str) -> ParsedSyllabus:
    """Step 1: Extract raw events from syllabus text."""
    client = _get_client()

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": EXTRACT_SYSTEM_PROMPT},
            {"role": "user", "content": syllabus_text},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    raw = json.loads(response.choices[0].message.content)
    return ParsedSyllabus(**raw)


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

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": STUDY_PLAN_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    raw = json.loads(response.choices[0].message.content)
    return StudyPlan(**raw)


def run_agent_pipeline(syllabus_text: str) -> StudyPlan:
    """Full agentic pipeline: Extract → Reason → Plan."""
    # Step 1: Extract events from syllabus
    parsed = extract_events(syllabus_text)

    # Step 2: Generate autonomous study plan
    plan = generate_study_plan(parsed)

    # Ensure the original syllabus events are included
    plan.syllabus_events = parsed.events

    return plan
