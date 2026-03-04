import os
from elevenlabs.client import ElevenLabs
from fastapi import UploadFile
import tempfile
import yt_dlp
import requests

def transcribe_file(file_path: str) -> str:
    """
    Uses ElevenLabs Speech-to-Text API to convert an audio file on disk to text.
    """
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY is not set in the environment variables.")

    client = ElevenLabs(api_key=api_key)

    with open(file_path, "rb") as audio_file:
        transcription = client.speech_to_text.convert(
            file=audio_file,
            model_id="scribe_v1"
        )
    return transcription.text

def transcribe_file_with_timestamps(file_path: str) -> list:
    """
    Uses ElevenLabs Speech-to-Text API to convert an audio file, extracting word-level timestamps.
    Returns a list of dictionaries: [{"word": "Text", "start": 0.0, "end": 1.2}, ...]
    """
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY is not set in the environment variables.")

    client = ElevenLabs(api_key=api_key)

    with open(file_path, "rb") as audio_file:
        transcription = client.speech_to_text.convert(
            file=audio_file,
            model_id="scribe_v1",
            language_code="en",
            timestamps_granularity="word" # Request word-level timestamps
        )
    
    # ElevenLabs scribe typically returns transcription.words which is a list of objects with text, start, end
    words_data = []
    if hasattr(transcription, 'words') and transcription.words:
        for w in transcription.words:
            words_data.append({
                "word": w.text,
                "start": w.start,
                "end": w.end
            })
    return words_data

def download_and_transcribe_supabase_url(url: str) -> str:
    """
    Downloads a public audio file hosted on Supabase Storage to a temporary file,
    transcribes it using ElevenLabs, and then cleans up the temporary file.
    """
    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    
    try:
        # Download the file from the public URL
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(temp_file.name, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        # Transcribe the downloaded file
        return transcribe_file(temp_file.name)
    finally:
        # Always clean up the local file to save disk space
        os.unlink(temp_file.name)

def download_and_transcribe_url(url: str) -> dict:
    """
    Downloads audio from a URL using yt-dlp, uploads it to Supabase Storage, 
    and transcribes it using ElevenLabs.
    """
    supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    supabase_key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    if not supabase_url or not supabase_key:
        raise ValueError("Supabase credentials are not set in the environment variables.")
        
    from supabase import create_client, Client
    supabase: Client = create_client(supabase_url, supabase_key)

    temp_dir = tempfile.mkdtemp()
    outtmpl = os.path.join(temp_dir, '%(id)s.%(ext)s')
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': outtmpl,
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_id = info_dict.get('id', 'audio')
            
            # Find the downloaded file
            audio_file = None
            for f in os.listdir(temp_dir):
                if f.startswith(video_id):
                    audio_file = os.path.join(temp_dir, f)
                    break
            
            if not audio_file:
                raise Exception("Failed to download audio from URL.")
                
            # Upload to Supabase
            file_ext = os.path.splitext(audio_file)[1]
            import time
            import random
            unique_filename = f"{video_id}_{int(time.time())}_{random.randint(1000, 9999)}{file_ext}"
            
            with open(audio_file, 'rb') as f:
                res = supabase.storage.from_('temporary-audio').upload(
                    file=f.read(),
                    path=unique_filename,
                    file_options={"content-type": "audio/mpeg"}
                )
                
            public_media_url = supabase.storage.from_('temporary-audio').get_public_url(unique_filename)
                
            # Transcribe the file
            transcript_text = transcribe_file(audio_file)
            
            return {
                "transcript": transcript_text,
                "media_url": public_media_url
            }
    finally:
        # Clean up temp directory
        for f in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, f))
        os.rmdir(temp_dir)

def clean_transcript(raw_text: str) -> str:
    """
    Cleans up conversational filler from the transcript so the AI has 
    a cleaner context window to extract hooks from.
    """
    # Simple heuristic cleaning for MVP speeds
    fillers = [" um ", " ah ", " like ", " you know ", " sort of ", " kinda "]
    cleaned = raw_text
    for filler in fillers:
        cleaned = cleaned.replace(filler, " ")
    
    # Remove extra spaces
    cleaned = " ".join(cleaned.split())
    return cleaned
