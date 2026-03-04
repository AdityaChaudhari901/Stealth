from pydantic import BaseModel, HttpUrl
from typing import Optional

class CaptionProcessRequest(BaseModel):
    video_url: str
    template_name: str = "viral_bold"
    language: str = "en"

class CaptionProcessResponse(BaseModel):
    project_id: str
    status: str

class ProjectStatusResponse(BaseModel):
    project_id: str
    status: str
    output_url: Optional[str] = None
    transcript: Optional[str] = None
