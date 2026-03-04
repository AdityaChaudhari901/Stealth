from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from . import elevenlabs as transcriber

router = APIRouter()

class TranscribeSupabaseRequest(BaseModel):
    url: str

@router.post("/transcribe-supabase")
async def transcribe_supabase_endpoint(payload: TranscribeSupabaseRequest):
    if not payload.url:
        raise HTTPException(status_code=400, detail="Supabase URL is required.")
    
    try:
        transcript_text = transcriber.download_and_transcribe_supabase_url(payload.url)
        cleaned_text = transcriber.clean_transcript(transcript_text)
        return {
            "status": "success",
            "transcript": transcript_text, 
            "cleaned_transcript": cleaned_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class TranscribeUrlRequest(BaseModel):
    url: str

@router.post("/transcribe-url")
async def transcribe_url_endpoint(payload: TranscribeUrlRequest):
    if not payload.url:
        raise HTTPException(status_code=400, detail="URL is required.")
    
    try:
        result = transcriber.download_and_transcribe_url(payload.url)
        transcript_text = result["transcript"]
        media_url = result["media_url"]
        
        cleaned_text = transcriber.clean_transcript(transcript_text)
        return {
            "status": "success",
            "transcript": transcript_text, 
            "cleaned_transcript": cleaned_text,
            "media_url": media_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
