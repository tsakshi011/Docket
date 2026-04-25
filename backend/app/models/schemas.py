from pydantic import BaseModel
from typing import Optional


class SyllabusEvent(BaseModel):
    title: str
    date: str  # ISO 8601: YYYY-MM-DD
    time: Optional[str] = None  # HH:MM (24h)
    duration_minutes: int = 60
    event_type: str  # exam, assignment, quiz, reading, lecture, lab, project, other
    description: str = ""
    weight: Optional[str] = None  # e.g., "20% of final grade"


class StudyBlock(BaseModel):
    title: str
    date: str  # ISO 8601: YYYY-MM-DD
    time: Optional[str] = None
    duration_minutes: int = 60
    block_type: str  # study_session, draft_deadline, outline, review, practice, break_down
    related_event: str  # title of the parent assignment/exam this supports
    description: str = ""
    priority: str = "medium"  # low, medium, high, critical


class ParsedSyllabus(BaseModel):
    course_name: str
    semester: str
    instructor: Optional[str] = None
    events: list[SyllabusEvent]


class StudyPlan(BaseModel):
    course_name: str
    semester: str
    syllabus_events: list[SyllabusEvent]
    study_blocks: list[StudyBlock]
    weekly_summary: list[str]  # high-level per-week summary
    warnings: list[str]  # e.g., "Heavy week: 3 deadlines on Nov 10-14"


class ParseRequest(BaseModel):
    openai_api_key: str


class ParseResponse(BaseModel):
    course_name: str
    semester: str
    instructor: Optional[str] = None
    syllabus_events: list[SyllabusEvent]
    study_blocks: list[StudyBlock]
    weekly_summary: list[str]
    warnings: list[str]
    raw_text_preview: str
