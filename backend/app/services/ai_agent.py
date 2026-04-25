from openai import OpenAI

from app.models.schemas import ParsedSyllabus, StudyPlan, StudyBlock

EXTRACT_SYSTEM_PROMPT = """You are an expert academic syllabus parser. Given the raw text of a course syllabus, extract ALL important dates and deadlines.

For each event provide:
- title: descriptive name (e.g., "Midterm Exam", "HW3 Due", "Final Project Proposal Due")
- date: ISO 8601 date string (YYYY-MM-DD). Infer the year from the semester/term context.
- time: start time if mentioned (HH:MM in 24h format), or null
- duration_minutes: estimated duration (120 for exams, 60 for quizzes, 30 for assignment submissions)
- event_type: one of "exam", "assignment", "quiz", "reading", "lecture", "lab", "project", "other"
- description: any additional context (room, chapter, instructions, format)
- weight: grade weight if mentioned (e.g., "20% of final grade")

Be thorough. Include assignment due dates, exam dates, project milestones, quiz dates, reading deadlines, and any other scheduled academic items. Resolve relative dates like "Week 5" using the semester start date."""

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

For each study block provide:
- title: descriptive action (e.g., "Study: Review Ch. 5-7 for Midterm", "Draft: Research Paper Outline")
- date: ISO 8601 date (YYYY-MM-DD)
- time: suggested time slot if possible, or null
- duration_minutes: realistic duration (45-120 min per block)
- block_type: one of "study_session", "draft_deadline", "outline", "review", "practice", "break_down", "research", "writing", "revision"
- related_event: the title of the parent assignment/exam
- description: specific instructions for what to do in this block
- priority: low, medium, high, or critical

Also provide:
- weekly_summary: a one-line summary for each week (e.g., "Week of Oct 14: Focus on Midterm prep, HW4 due Wednesday")
- warnings: alert about heavy weeks, conflicting deadlines, or tight turnarounds"""


def extract_events(syllabus_text: str, api_key: str) -> ParsedSyllabus:
    """Step 1: Extract raw events from syllabus text."""
    client = OpenAI(api_key=api_key)

    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": EXTRACT_SYSTEM_PROMPT},
            {"role": "user", "content": syllabus_text},
        ],
        response_format=ParsedSyllabus,
    )

    return response.choices[0].message.parsed


def generate_study_plan(parsed: ParsedSyllabus, api_key: str) -> StudyPlan:
    """Step 2: Generate an autonomous study plan based on extracted events."""
    client = OpenAI(api_key=api_key)

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

    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": STUDY_PLAN_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format=StudyPlan,
    )

    return response.choices[0].message.parsed


def run_agent_pipeline(syllabus_text: str, api_key: str) -> StudyPlan:
    """Full agentic pipeline: Extract → Reason → Plan."""
    # Step 1: Extract events from syllabus
    parsed = extract_events(syllabus_text, api_key)

    # Step 2: Generate autonomous study plan
    plan = generate_study_plan(parsed, api_key)

    # Ensure the original syllabus events are included
    plan.syllabus_events = parsed.events

    return plan
