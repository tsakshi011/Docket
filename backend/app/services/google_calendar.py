import logging
from datetime import datetime, timedelta

import httpx

from app.models.schemas import StudyBlock, SyllabusEvent

logger = logging.getLogger(__name__)

GCAL_API = "https://www.googleapis.com/calendar/v3"

EVENT_TYPE_COLORS: dict[str, str] = {
    "exam": "11",        # tomato
    "assignment": "9",   # blueberry
    "quiz": "6",         # tangerine
    "project": "3",      # grape
    "reading": "2",      # sage
    "lecture": "8",      # graphite
    "lab": "7",          # peacock
    "other": "8",        # graphite
}

PRIORITY_COLORS: dict[str, str] = {
    "critical": "11",  # tomato
    "high": "6",       # tangerine
    "medium": "9",     # blueberry
    "low": "8",        # graphite
}

TIMEZONE = "America/Los_Angeles"


def _build_datetime(date: str, time: str | None) -> str:
    if time:
        return f"{date}T{time}:00"
    return f"{date}T09:00:00"


def _end_datetime(date: str, time: str | None, duration_minutes: int) -> str:
    start = datetime.fromisoformat(_build_datetime(date, time))
    end = start + timedelta(minutes=duration_minutes)
    return end.strftime("%Y-%m-%dT%H:%M:%S")


def syllabus_event_to_gcal(ev: SyllabusEvent) -> dict:
    desc = ev.description or f"Type: {ev.event_type}"
    if ev.weight:
        desc += f"\nWeight: {ev.weight}"

    return {
        "summary": ev.title,
        "start": {"dateTime": _build_datetime(ev.date, ev.time), "timeZone": TIMEZONE},
        "end": {"dateTime": _end_datetime(ev.date, ev.time, ev.duration_minutes), "timeZone": TIMEZONE},
        "description": desc,
        "colorId": EVENT_TYPE_COLORS.get(ev.event_type, "8"),
    }


def study_block_to_gcal(block: StudyBlock) -> dict:
    desc = block.description or ""
    desc += f"\nFor: {block.related_event}\nPriority: {block.priority}"

    return {
        "summary": block.title,
        "start": {"dateTime": _build_datetime(block.date, block.time), "timeZone": TIMEZONE},
        "end": {"dateTime": _end_datetime(block.date, block.time, block.duration_minutes), "timeZone": TIMEZONE},
        "description": desc.strip(),
        "colorId": PRIORITY_COLORS.get(block.priority, "8"),
    }


async def create_calendar(name: str, access_token: str) -> dict:
    """Create a new secondary Google Calendar and return its metadata."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{GCAL_API}/calendars",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"summary": name, "timeZone": TIMEZONE},
        )
        resp.raise_for_status()
        return resp.json()


async def insert_event(calendar_id: str, event: dict, access_token: str) -> dict:
    """Insert a single event into a Google Calendar."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{GCAL_API}/calendars/{calendar_id}/events",
            headers={"Authorization": f"Bearer {access_token}"},
            json=event,
        )
        resp.raise_for_status()
        return resp.json()


async def export_plan_to_google_calendar(
    course_name: str,
    syllabus_events: list[SyllabusEvent],
    study_blocks: list[StudyBlock],
    access_token: str,
) -> dict:
    """Create a Google Calendar and populate it with the full study plan.

    Returns ``{"calendar_id": ..., "calendar_url": ..., "events_created": int}``.
    """
    cal = await create_calendar(f"{course_name} - Study Plan", access_token)
    calendar_id = cal["id"]

    created = 0
    for ev in syllabus_events:
        await insert_event(calendar_id, syllabus_event_to_gcal(ev), access_token)
        created += 1

    for block in study_blocks:
        await insert_event(calendar_id, study_block_to_gcal(block), access_token)
        created += 1

    logger.info("Created %d events in calendar %s", created, calendar_id)

    return {
        "calendar_id": calendar_id,
        "calendar_url": f"https://calendar.google.com/calendar/r?cid={calendar_id}",
        "events_created": created,
    }
