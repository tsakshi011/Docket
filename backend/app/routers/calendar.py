import json
import logging

from fastapi import APIRouter, HTTPException
from httpx import HTTPStatusError

from app.models.schemas import CalendarExportRequest, CalendarExportResponse
from app.services.google_calendar import export_plan_to_google_calendar

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["calendar"])


def _parse_gcal_error(response_text: str) -> dict | None:
    """Extract structured error info from a Google API JSON response."""
    try:
        body = json.loads(response_text)
        return body.get("error")
    except (json.JSONDecodeError, AttributeError):
        return None


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

        if status == 403:
            error_info = _parse_gcal_error(detail)
            if error_info:
                details = error_info.get("details", [])
                for d in details:
                    if d.get("reason") == "SERVICE_DISABLED":
                        activation_url = d.get("metadata", {}).get(
                            "activationUrl", ""
                        )
                        msg = (
                            "The Google Calendar API is not enabled for your "
                            "Google Cloud project. Please enable it at: "
                            + activation_url
                            + " — then wait a minute and try again."
                        )
                        raise HTTPException(403, msg)
            raise HTTPException(
                403,
                "Access denied by Google Calendar API. Please check that the "
                "Calendar API is enabled in your Google Cloud project and that "
                "your account has the required permissions.",
            )

        raise HTTPException(status, f"Google Calendar API error: {detail}")

    return result
