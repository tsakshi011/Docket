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


def _build_datetime(date: str, time: str | None) -> str:
    t = time if time else "09:00"
    return f"{date}T{t}:00"


def syllabus_event_to_gcal(ev: SyllabusEvent) -> dict:
    start = _build_datetime(ev.date, ev.time)
    return {
        "summary": f"\U0001f4cc {ev.title}",
        "description": (ev.description or f"Type: {ev.event_type}")
        + (f"\nWeight: {ev.weight}" if ev.weight else ""),
        "start": {"dateTime": start, "timeZone": "America/Los_Angeles"},
        "end": {
            "dateTime": _build_datetime(ev.date, ev.time).replace(
                ev.time or "09:00",
                f"{int((ev.time or '09:00').split(':')[0]) + ev.duration_minutes // 60:02d}:{int((ev.time or '09:00').split(':')[1]) + ev.duration_minutes % 60:02d}",
            ),
            "timeZone": "America/Los_Angeles",
        },
        "colorId": EVENT_TYPE_COLORS.get(ev.event_type, "8"),
    }


def study_block_to_gcal(block: StudyBlock) -> dict:
    start = _build_datetime(block.date, block.time)
    return {
        "summary": f"\U0001f4da {block.title}",
        "description": (block.description or "")
        + f"\nFor: {block.related_event}\nPriority: {block.priority}",
        "start": {"dateTime": start, "timeZone": "America/Los_Angeles"},
        "end": {
            "dateTime": _build_datetime(block.date, block.time).replace(
                block.time or "09:00",
                f"{int((block.time or '09:00').split(':')[0]) + block.duration_minutes // 60:02d}:{int((block.time or '09:00').split(':')[1]) + block.duration_minutes % 60:02d}",
            ),
            "timeZone": "America/Los_Angeles",
        },
        "colorId": PRIORITY_COLORS.get(block.priority, "9"),
    }


async def create_calendar(name: str, token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{CALENDAR_API}/calendars",
            headers=_headers(token),
            json={"summary": name, "timeZone": "America/Los_Angeles"},
        )
        resp.raise_for_status()
        return resp.json()


async def insert_event(calendar_id: str, event_body: dict, token: str) -> dict:
    async with httpx.AsyncClient() as client:
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
    cal = await create_calendar(f"{course_name} - Study Plan", access_token)
    calendar_id = cal["id"]
    created = 0

    for ev in syllabus_events:
        await insert_event(calendar_id, syllabus_event_to_gcal(ev), access_token)
        created += 1

    for block in study_blocks:
        await insert_event(calendar_id, study_block_to_gcal(block), access_token)
        created += 1

    return {
        "calendar_id": calendar_id,
        "calendar_url": f"https://calendar.google.com/calendar/r?cid={calendar_id}",
        "events_created": created,
    }
