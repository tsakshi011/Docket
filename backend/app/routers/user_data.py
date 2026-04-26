import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user-data", tags=["user-data"])

_NO_DB_MSG = (
    "Database not configured — data is only stored in your browser. "
    "Set MONGODB_URI in the backend .env file to enable cloud persistence."
)


class SaveCourseRequest(BaseModel):
    uid: str
    course_name: str
    course_data: dict


class SaveTaskProgressRequest(BaseModel):
    uid: str
    course_name: str
    completed_items: list[str]
    custom_tasks: list[dict]


class ColdCallRequest(BaseModel):
    uid: str
    course_name: str


@router.get("/{uid}/courses")
async def get_user_courses(uid: str):
    db = get_db()
    if db is None:
        return {"courses": [], "task_progress": {}, "cold_calls": {}}

    doc = await db.user_data.find_one({"uid": uid}, {"_id": 0})
    if not doc:
        return {"courses": [], "task_progress": {}, "cold_calls": {}}
    return {
        "courses": doc.get("courses", []),
        "task_progress": doc.get("task_progress", {}),
        "cold_calls": doc.get("cold_calls", {}),
    }


@router.put("/courses")
async def save_course(req: SaveCourseRequest):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail=_NO_DB_MSG)

    now = datetime.now(timezone.utc)

    existing = await db.user_data.find_one({"uid": req.uid})
    if existing:
        courses = existing.get("courses", [])
        courses = [c for c in courses if c.get("name") != req.course_name]
        courses.append({
            "name": req.course_name,
            "data": req.course_data,
            "updated_at": now.isoformat(),
        })
        await db.user_data.update_one(
            {"uid": req.uid},
            {"$set": {"courses": courses, "updated_at": now}},
        )
    else:
        await db.user_data.insert_one({
            "uid": req.uid,
            "courses": [{
                "name": req.course_name,
                "data": req.course_data,
                "updated_at": now.isoformat(),
            }],
            "task_progress": {},
            "created_at": now,
            "updated_at": now,
        })

    return {"status": "ok"}


@router.delete("/{uid}/courses/{course_name}")
async def delete_course(uid: str, course_name: str):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail=_NO_DB_MSG)

    await db.user_data.update_one(
        {"uid": uid},
        {
            "$pull": {"courses": {"name": course_name}},
            "$unset": {f"task_progress.{course_name}": ""},
        },
    )
    return {"status": "ok"}


@router.put("/tasks")
async def save_task_progress(req: SaveTaskProgressRequest):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail=_NO_DB_MSG)

    now = datetime.now(timezone.utc)
    safe_key = req.course_name.replace(".", "_").replace("$", "_")
    await db.user_data.update_one(
        {"uid": req.uid},
        {
            "$set": {
                f"task_progress.{safe_key}": {
                    "completed_items": req.completed_items,
                    "custom_tasks": req.custom_tasks,
                },
                "updated_at": now,
            }
        },
        upsert=True,
    )
    return {"status": "ok"}


@router.put("/cold-call")
async def record_cold_call(req: ColdCallRequest):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail=_NO_DB_MSG)

    now = datetime.now(timezone.utc)
    safe_key = req.course_name.replace(".", "_").replace("$", "_")
    await db.user_data.update_one(
        {"uid": req.uid},
        {
            "$set": {
                f"cold_calls.{safe_key}": now.isoformat(),
                "updated_at": now,
            }
        },
        upsert=True,
    )
    return {"status": "ok", "date": now.isoformat()}
