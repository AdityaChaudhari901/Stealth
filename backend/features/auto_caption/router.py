from fastapi import APIRouter, BackgroundTasks, HTTPException
from .schemas import CaptionProcessRequest, CaptionProcessResponse, ProjectStatusResponse
from .service import process_video_task
from core.supabase import supabase

router = APIRouter()

@router.post("/process", response_model=CaptionProcessResponse)
def process_video(request: CaptionProcessRequest, background_tasks: BackgroundTasks):
    """
    Submits a new video for auto-caption processing.
    """
    try:
        # 1. Create a tracking record in Supabase `projects` table
        # We assume user_id is handled if they passed a token, but for MVP without strict backend auth yet, we'll insert a standard null or use service role structure
        # In a real app, extract user_id from FastAPI auth middleware
        record = supabase.table("projects").insert({
            "video_url": request.video_url,
            "template_name": request.template_name,
            "language": request.language,
            "status": "processing"
        }).execute()

        if len(record.data) == 0:
            raise HTTPException(status_code=500, detail="Failed to create project record in database")
            
        project_id = record.data[0]['id']

        # 2. Dispatch background task
        background_tasks.add_task(
            process_video_task,
            project_id=project_id,
            video_url=request.video_url,
            template_name=request.template_name,
            language=request.language
        )

        return CaptionProcessResponse(project_id=project_id, status="processing")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{project_id}", response_model=ProjectStatusResponse)
def get_project_status(project_id: str):
    """
    Polls the status of the background task.
    """
    try:
        response = supabase.table("projects").select("id, status, output_url, transcript_json").eq("id", project_id).execute()
        
        if len(response.data) == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        
        data = response.data[0]
        
        # Optionally return transcript if needed by frontend
        transcript_text = None
        if data.get("transcript_json"):
            # Mock extraction or real extraction depending on structure
            pass
            
        return ProjectStatusResponse(
            project_id=data["id"],
            status=data["status"],
            output_url=data.get("output_url"),
            transcript=transcript_text
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
