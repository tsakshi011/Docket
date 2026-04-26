from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    ParsedSyllabus,
    ResourceRecommendations,
    ResourceRequest,
)
from app.services.resource_agent import recommend_resources

router = APIRouter(prefix="/api/resources", tags=["resources"])


@router.post("/recommend", response_model=ResourceRecommendations)
async def recommend(req: ResourceRequest):
    """Standalone endpoint to get resource recommendations.

    Useful when the user already has a parsed syllabus and wants to
    refresh or fetch resources independently of the full parse pipeline.
    """
    parsed = ParsedSyllabus(
        course_name=req.course_name,
        semester=req.semester,
        events=req.events,
    )
    try:
        return recommend_resources(parsed)
    except Exception as e:
        raise HTTPException(500, f"Resource agent failed: {str(e)}")
