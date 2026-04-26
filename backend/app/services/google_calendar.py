from datetime import datetime, timedelta

import httpx

from app.models.schemas import SyllabusEvent, StudyBlock

CALENDAR_API = "https://www.googleapis.com/calendar/v3"

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
    "critical": "11",    # tomato
    "high": "6",         # tangerine
    "medium": "9",       # blueberry
    "low": "2",          # sage
}


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _start_end(date: str, time: str | None, duration_minutes: int) -> tuple[str, str]:
    t = time if time else "09:00"
    start_dt = datetime.fromisoformat(f"{date}T{t}:00")
    end_dt = start_dt + timedelta(minutes=duration_minutes)
    fmt = "%Y-%m-%dT%H:%M:%S"
    return start_dt.strftime(fmt), end_dt.strftime(fmt)


def syllabus_event_to_gcal(ev: SyllabusEvent) -> dict:
    start, end = _start_end(ev.date, ev.time, ev.duration_minutes)
    return {
        "summary": f"\U0001f4cc {ev.title}",
        "description": (ev.description or f"Type: {ev.event_type}")
        + (f"\nWeight: {ev.weight}" if ev.weight else ""),
        "start": {"dateTime": start, "timeZone": "America/Los_Angeles"},
        "end": {"dateTime": end, "timeZone": "America/Los_Angeles"},
        "colorId": EVENT_TYPE_COLORS.get(ev.event_type, "8"),
    }


def study_block_to_gcal(block: StudyBlock) -> dict:
    start, end = _start_end(block.date, block.time, block.duration_minutes)
    return {
        "summary": f"\U0001f4da {block.title}",
        "description": (block.description or "")
        + f"\nFor: {block.related_event}\nPriority: {block.priority}",
        "start": {"dateTime": start, "timeZone": "America/Los_Angeles"},
        "end": {"dateTime": end, "timeZone": "America/Los_Angeles"},
        "colorId": PRIORITY_COLORS.get(block.priority, "9"),
    }


GCAL_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


async def create_calendar(
    name: str, token: str, client: httpx.AsyncClient,
) -> dict:
    resp = await client.post(
        f"{CALENDAR_API}/calendars",
        headers=_headers(token),
        json={"summary": name, "timeZone": "America/Los_Angeles"},
    )
    resp.raise_for_status()
    return resp.json()


async def insert_event(
    calendar_id: str, event_body: dict, token: str, client: httpx.AsyncClient,
) -> dict:
    resp = await client.post(
        f"{CALENDAR_API}/calendars/{calendar_id}/events",
        headers=_headers(token),
        json=event_body,
    )
    resp.raise_for_status()
    return resp.json()


async def export_plan_to_google_calendar(
    course_name: str,
    syllabus_events: list[SyllabusEvent],
    study_blocks: list[StudyBlock],
    access_token: str,
) -> dict:
    async with httpx.AsyncClient(timeout=GCAL_TIMEOUT) as client:
        cal = await create_calendar(
            f"{course_name} - Study Plan", access_token, client,
        )
        calendar_id = cal["id"]
        created = 0

        for ev in syllabus_events:
            await insert_event(
                calendar_id, syllabus_event_to_gcal(ev), access_token, client,
            )
            created += 1

        for block in study_blocks:
            await insert_event(
                calendar_id, study_block_to_gcal(block), access_token, client,
            )
            created += 1

    return {
        "calendar_id": calendar_id,
        "calendar_url": f"https://calendar.google.com/calendar/r?cid={calendar_id}",
        "events_created": created,
    }
