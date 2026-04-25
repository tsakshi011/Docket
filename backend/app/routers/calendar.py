import logging

from fastapi import APIRouter, HTTPException
from httpx import HTTPStatusError

from app.models.schemas import CalendarExportRequest, CalendarExportResponse
from app.services.google_calendar import export_plan_to_google_calendar

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["calendar"])


@router.post("/calendar/export", response_model=CalendarExportResponse)
async def export_to_google_calendar(req: CalendarExportRequest):
    """Create a new Google Calendar populated with the full study plan."""
    try:
        result = await export_plan_to_google_calendar(
            course_name=req.course_name,
            syllabus_events=req.syllabus_events,
            study_blocks=req.study_blocks,
            access_token=req.access_token,
        )
    except HTTPStatusError as exc:
        status = exc.response.status_code
        detail = exc.response.text
        logger.error("Google Calendar API error %s: %s", status, detail)
        if status == 401:
            raise HTTPException(
                401,
                "Google token expired or invalid. Please sign in again.",
            )
        raise HTTPException(status, f"Google Calendar API error: {detail}")

    return result
