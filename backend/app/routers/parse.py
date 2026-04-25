from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response

from app.services.pdf_parser import extract_text_from_pdf
from app.services.ai_agent import run_agent_pipeline
from app.services.calendar_export import generate_ics
from app.models.schemas import ParseResponse

router = APIRouter(prefix="/api", tags=["parse"])


@router.post("/parse", response_model=ParseResponse)
async def parse_syllabus(
    file: UploadFile = File(...),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Please upload a PDF file.")

    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(400, "File too large. Max 10MB.")

    # Step 1: Extract text
    syllabus_text = extract_text_from_pdf(file_bytes)
    if not syllabus_text.strip():
        raise HTTPException(
            400,
            "Could not extract text from this PDF. It may be a scanned image — try a text-based PDF.",
        )

    # Step 2+3: Run agentic pipeline (extract events → generate study plan)
    try:
        plan = run_agent_pipeline(syllabus_text)
    except Exception as e:
        raise HTTPException(500, f"AI processing failed: {str(e)}")

    return ParseResponse(
        course_name=plan.course_name,
        semester=plan.semester,
        syllabus_events=plan.syllabus_events,
        study_blocks=plan.study_blocks,
        weekly_summary=plan.weekly_summary,
        warnings=plan.warnings,
        raw_text_preview=syllabus_text[:500],
    )


@router.post("/export/ics")
async def export_ics(
    file: UploadFile = File(...),
):
    """Parse syllabus and return a downloadable .ics file."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Please upload a PDF file.")

    file_bytes = await file.read()
    syllabus_text = extract_text_from_pdf(file_bytes)
    if not syllabus_text.strip():
        raise HTTPException(400, "Could not extract text from this PDF.")

    try:
        plan = run_agent_pipeline(syllabus_text)
    except Exception as e:
        raise HTTPException(500, f"AI processing failed: {str(e)}")

    ics_content = generate_ics(
        plan.course_name, plan.syllabus_events, plan.study_blocks
    )

    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f'attachment; filename="{plan.course_name.replace(" ", "_")}_study_plan.ics"'
        },
    )
