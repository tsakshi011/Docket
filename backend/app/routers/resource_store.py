"""CRUD endpoints for persisting AI-generated study resources in MongoDB.

Collection: ``resources``
Document shape::

    {
        "uid":             "firebase-uid",
        "course_name":     "CS 101",
        "subject_domain":  "computer_science",
        "general_resources": [ ... ],
        "topic_resources":  [ ... ],
        "study_tips":       [ ... ],
        "created_at":       ISODate,
        "updated_at":       ISODate,
    }

Compound unique index on ``(uid, course_name)`` so each user has at most
one resource document per course.  Upserting replaces the whole payload
while preserving ``created_at``.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.database import get_db
from app.models.schemas import (
    DeleteResourceRequest,
    ResourceRecommendations,
    SaveResourcesRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resources", tags=["resource-store"])

_NO_DB_MSG = (
    "Database not configured — resources are only stored in your browser. "
    "Set MONGODB_URI in the backend .env file to enable cloud persistence."
)


@router.put("/store")
async def save_resources(req: SaveResourcesRequest):
    """Upsert the full resource recommendations for a user + course."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail=_NO_DB_MSG)

    now = datetime.now(timezone.utc)
    payload = req.resources.model_dump()

    # Deduplicate resources by URL within each list
    payload["general_resources"] = _dedupe_resources(
        payload.get("general_resources", [])
    )
    for topic in payload.get("topic_resources", []):
        topic["resources"] = _dedupe_resources(topic.get("resources", []))

    await db.resources.update_one(
        {"uid": req.uid, "course_name": req.course_name},
        {
            "$set": {
                **payload,
                "updated_at": now,
            },
            "$setOnInsert": {
                "uid": req.uid,
                "course_name": req.course_name,
                "created_at": now,
            },
        },
        upsert=True,
    )
    return {"status": "ok", "updated_at": now.isoformat()}


@router.get("/store/{uid}/{course_name}", response_model=ResourceRecommendations | None)
async def get_resources(uid: str, course_name: str):
    """Fetch stored resources for a user + course.

    Returns ``null`` (204) if nothing is stored yet.
    """
    db = get_db()
    if db is None:
        return None

    doc = await db.resources.find_one(
        {"uid": uid, "course_name": course_name},
        {"_id": 0, "uid": 0, "created_at": 0, "updated_at": 0},
    )
    if not doc:
        return None

    return ResourceRecommendations(**doc)


@router.get("/store/{uid}", response_model=dict)
async def get_all_resources(uid: str):
    """Fetch all stored resources for a user, keyed by course name."""
    db = get_db()
    if db is None:
        return {"resources": {}}

    cursor = db.resources.find(
        {"uid": uid},
        {"_id": 0, "uid": 0, "created_at": 0, "updated_at": 0},
    )
    result: dict[str, dict] = {}
    async for doc in cursor:
        cname = doc.pop("course_name", "unknown")
        result[cname] = doc
    return {"resources": result}


@router.delete("/store")
async def delete_resource(req: DeleteResourceRequest):
    """Delete a specific resource or an entire course's resources.

    - If neither ``resource_url``/``resource_title`` nor ``topic`` is given,
      the entire course document is removed.
    - If ``topic`` is given (but no resource identifiers), the whole topic
      section is removed.
    - If ``resource_url`` or ``resource_title`` is given, that single
      resource is pulled from general_resources and every topic's list.
    """
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail=_NO_DB_MSG)

    filt = {"uid": req.uid, "course_name": req.course_name}

    # Full delete
    if not req.resource_url and not req.resource_title and not req.topic:
        result = await db.resources.delete_one(filt)
        return {"status": "ok", "deleted": result.deleted_count}

    doc = await db.resources.find_one(filt)
    if not doc:
        raise HTTPException(status_code=404, detail="No resources found for this course")

    changed = False

    # Remove an entire topic section
    if req.topic and not req.resource_url and not req.resource_title:
        before = len(doc.get("topic_resources", []))
        doc["topic_resources"] = [
            t for t in doc.get("topic_resources", [])
            if t.get("topic", "").lower() != req.topic.lower()
        ]
        changed = len(doc["topic_resources"]) < before

    # Remove a single resource by URL or title
    if req.resource_url or req.resource_title:
        def keep(r: dict) -> bool:
            if req.resource_url and r.get("url") == req.resource_url:
                return False
            if req.resource_title and r.get("title") == req.resource_title:
                return False
            return True

        before_gen = len(doc.get("general_resources", []))
        doc["general_resources"] = [r for r in doc.get("general_resources", []) if keep(r)]
        if len(doc["general_resources"]) < before_gen:
            changed = True

        for topic in doc.get("topic_resources", []):
            before_t = len(topic.get("resources", []))
            topic["resources"] = [r for r in topic.get("resources", []) if keep(r)]
            if len(topic["resources"]) < before_t:
                changed = True

    if changed:
        now = datetime.now(timezone.utc)
        await db.resources.update_one(
            filt,
            {"$set": {
                "general_resources": doc["general_resources"],
                "topic_resources": doc["topic_resources"],
                "updated_at": now,
            }},
        )
    return {"status": "ok", "changed": changed}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dedupe_resources(resources: list[dict]) -> list[dict]:
    """Remove duplicate resources, preferring the first occurrence.

    Deduplication key: URL if present, otherwise title.
    """
    seen: set[str] = set()
    out: list[dict] = []
    for r in resources:
        key = r.get("url") or r.get("title", "")
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out
