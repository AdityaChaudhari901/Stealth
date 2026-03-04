from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from . import generator
from features.transcription import elevenlabs as transcriber

router = APIRouter()

class GenerateRequest(BaseModel):
    content: str
    inputType: str

@router.post("/generate")
async def generate_content(payload: GenerateRequest):
    # Process the transcript
    if payload.inputType == "transcript":
        transcript = payload.content
    else:
        transcript = transcriber.transcribe_audio(payload.content)

    cleaned_transcript = transcriber.clean_transcript(transcript)
    
    # Generate the assets using the AI module
    hooks = generator.generate_hooks(cleaned_transcript, count=10)
    scripts = generator.generate_scripts(hooks, cleaned_transcript)
    social_posts = generator.generate_social_posts(cleaned_transcript)
    show_notes = generator.generate_show_notes(cleaned_transcript)
    newsletter = generator.generate_newsletter(cleaned_transcript)

    return {
        "status": "success", 
        "data": {
            "hooks": hooks,
            "scripts": scripts,
            "social": social_posts,
            "show_notes": show_notes,
            "newsletter": newsletter
        }
    }
