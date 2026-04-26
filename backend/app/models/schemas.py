import re

from pydantic import BaseModel, field_validator
from typing import Optional

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME_RE = re.compile(r"^\d{2}:\d{2}$")


def _validate_date(v: str) -> str:
    if not _DATE_RE.match(v):
        return "2099-01-01"
    return v


def _validate_time(v: str | None) -> str | None:
    if v is not None and not _TIME_RE.match(v):
        return None
    return v


class SyllabusEvent(BaseModel):
    title: str
    date: str  # ISO 8601: YYYY-MM-DD
    time: Optional[str] = None  # HH:MM (24h)
    duration_minutes: int = 60
    event_type: str  # exam, assignment, quiz, reading, lecture, lab, project, other
    description: Optional[str] = ""
    weight: Optional[str] = None  # e.g., "20% of final grade"

    @field_validator("date")
    @classmethod
    def check_date(cls, v: str) -> str:
        return _validate_date(v)

    @field_validator("time")
    @classmethod
    def check_time(cls, v: str | None) -> str | None:
        return _validate_time(v)


class StudyBlock(BaseModel):
    title: str
    date: str  # ISO 8601: YYYY-MM-DD
    time: Optional[str] = None
    duration_minutes: int = 60
    block_type: str  # study_session, draft_deadline, outline, review, practice, break_down
    related_event: str  # title of the parent assignment/exam this supports
    description: Optional[str] = ""
    priority: str = "medium"  # low, medium, high, critical

    @field_validator("date")
    @classmethod
    def check_date(cls, v: str) -> str:
        return _validate_date(v)

    @field_validator("time")
    @classmethod
    def check_time(cls, v: str | None) -> str | None:
        return _validate_time(v)


class ParsedSyllabus(BaseModel):
    course_name: str
    semester: str
    instructor: Optional[str] = None
    events: list[SyllabusEvent]


class StudyPlan(BaseModel):
    course_name: str
    semester: str
    syllabus_events: list[SyllabusEvent]
    study_blocks: list[StudyBlock] = []
    weekly_summary: list[str] = [] # high-level per-week summary
    warnings: list[str] = [] # e.g., "Heavy week: 3 deadlines on Nov 10-14"


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


class CalendarExportRequest(BaseModel):
    course_name: str
    access_token: str
    syllabus_events: list[SyllabusEvent]
    study_blocks: list[StudyBlock]


class CalendarExportResponse(BaseModel):
    calendar_id: str
    calendar_url: str
    events_created: int
