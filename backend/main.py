import os
import sys
from dotenv import load_dotenv

# Load environment variables
backend_env = os.path.join(os.path.dirname(__file__), '.env')
frontend_env = os.path.join(os.path.dirname(__file__), '..', 'frontend', '.env.local')

load_dotenv(dotenv_path=backend_env)
load_dotenv(dotenv_path=frontend_env) # Load the Public Supabase config so backend yt-dlp can use it

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from features.auto_caption.router import router as caption_router
from features.transcription.router import router as transcription_router
from features.podcast_repurposer.router import router as repurposer_router

app = FastAPI(title="AI Content Repurposing Engine")

app.include_router(caption_router, prefix="/api/caption", tags=["Captioning"])
app.include_router(transcription_router, prefix="/api", tags=["Transcription"])
app.include_router(repurposer_router, prefix="/api", tags=["Repurposer"])

# Configure CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "AI Content Repurposing API is running"}
