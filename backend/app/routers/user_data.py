from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import get_db

router = APIRouter(prefix="/api/user-data", tags=["user-data"])


class SaveCourseRequest(BaseModel):
    uid: str
    course_name: str
    course_data: dict


class SaveTaskProgressRequest(BaseModel):
    uid: str
    course_name: str
    completed_items: list[str]
    custom_tasks: list[dict]


@router.get("/{uid}/courses")
async def get_user_courses(uid: str):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")

    doc = await db.user_data.find_one({"uid": uid}, {"_id": 0})
    if not doc:
        return {"courses": [], "task_progress": {}}
    return {
        "courses": doc.get("courses", []),
        "task_progress": doc.get("task_progress", {}),
    }


@router.put("/courses")
async def save_course(req: SaveCourseRequest):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")

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
        raise HTTPException(status_code=503, detail="Database not configured")

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
        raise HTTPException(status_code=503, detail="Database not configured")

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
