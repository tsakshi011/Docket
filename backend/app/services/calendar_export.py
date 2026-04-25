from datetime import datetime, timedelta
from icalendar import Calendar, Event as ICalEvent
from urllib.parse import urlencode

from app.models.schemas import SyllabusEvent, StudyBlock


def _parse_dt(date_str: str, time_str: str | None) -> datetime:
    if time_str:
        return datetime.fromisoformat(f"{date_str}T{time_str}:00")
    return datetime.fromisoformat(f"{date_str}T09:00:00")


def generate_ics(
    course_name: str,
    syllabus_events: list[SyllabusEvent],
    study_blocks: list[StudyBlock],
) -> str:
    """Generate an .ics file containing all syllabus events and study blocks."""
    cal = Calendar()
    cal.add("prodid", "-//SyllabusToCalendar//EN")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", f"{course_name} - Study Plan")

    for ev in syllabus_events:
        event = ICalEvent()
        event.add("summary", f"📌 {ev.title}")
        start = _parse_dt(ev.date, ev.time)
        event.add("dtstart", start)
        event.add("dtend", start + timedelta(minutes=ev.duration_minutes))
        event.add("description", ev.description or f"Type: {ev.event_type}")
        if ev.weight:
            event["description"] += f"\nWeight: {ev.weight}"
        cal.add_component(event)

    for block in study_blocks:
        event = ICalEvent()
        event.add("summary", f"📚 {block.title}")
        start = _parse_dt(block.date, block.time)
        event.add("dtstart", start)
        event.add("dtend", start + timedelta(minutes=block.duration_minutes))
        desc = block.description or ""
        desc += f"\nFor: {block.related_event}\nPriority: {block.priority}"
        event.add("description", desc.strip())
        cal.add_component(event)

    return cal.to_ical().decode("utf-8")


def generate_gcal_link(event_title: str, date: str, time: str | None, duration_minutes: int, description: str = "") -> str:
    """Generate a Google Calendar 'Add Event' URL."""
    start = _parse_dt(date, time)
    end = start + timedelta(minutes=duration_minutes)
    fmt = "%Y%m%dT%H%M%S"

    params = {
        "action": "TEMPLATE",
        "text": event_title,
        "dates": f"{start.strftime(fmt)}/{end.strftime(fmt)}",
        "details": description,
    }
    return f"https://calendar.google.com/calendar/render?{urlencode(params)}"
