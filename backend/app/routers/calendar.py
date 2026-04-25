import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.models.schemas import PlanStoreRequest, PlanStoreResponse
from app.services.calendar_export import generate_ics

router = APIRouter(prefix="/api", tags=["calendar"])

# In-memory store for plans. Replace with a database for production.
_plans: dict[str, PlanStoreRequest] = {}


@router.post("/plans", response_model=PlanStoreResponse)
async def store_plan(req: PlanStoreRequest):
    """Store a study plan and return a plan_id for the ICS feed URL."""
    plan_id = uuid.uuid4().hex[:12]
    _plans[plan_id] = req
    return PlanStoreResponse(plan_id=plan_id)


@router.get("/plans/{plan_id}/calendar.ics")
async def get_plan_ics(plan_id: str):
    """Serve the study plan as an ICS feed that Google Calendar can subscribe to."""
    plan = _plans.get(plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found.")

    ics_content = generate_ics(
        plan.course_name, plan.syllabus_events, plan.study_blocks
    )

    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f'inline; filename="{plan.course_name.replace(" ", "_")}_study_plan.ics"',
            "Cache-Control": "no-cache",
        },
    )
