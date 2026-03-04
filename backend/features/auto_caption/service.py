import os
import tempfile
import logging
import requests

from core.supabase import supabase
from features.transcription import elevenlabs as transcriber
from . import ffmpeg as ffu

logger = logging.getLogger(__name__)

def download_file(url: str, output_path: str):
    """Downloads a file from a URL to a local path."""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

def process_video_task(project_id: str, video_url: str, template_name: str, language: str):
    """
    Complete Background task to process an auto-captioning video job.
    """
    logger.info(f"Starting video processing for project {project_id}")
    
    # Create an isolated temporary directory for all working files
    temp_dir = tempfile.mkdtemp()
    
    local_video_path = os.path.join(temp_dir, "input.mp4")
    local_audio_path = os.path.join(temp_dir, "audio.wav")
    local_ass_path = os.path.join(temp_dir, "captions.ass")
    local_output_path = os.path.join(temp_dir, "output.mp4")
    
    try:
        supabase.table("projects").update({"status": "processing"}).eq("id", project_id).execute()
        
        # 1. Download Video
        logger.info(f"Downloading video from {video_url}")
        download_file(video_url, local_video_path)
        
        # 2. Extract Audio via FFmpeg
        logger.info("Extracting audio")
        success = ffu.extract_audio(local_video_path, local_audio_path)
        if not success:
            raise Exception("Failed to extract audio from video.")
            
        # 3. Transcribe with ElevenLabs (Timestamped Words)
        logger.info("Transcribing audio with ElevenLabs")
        words_data = transcriber.transcribe_file_with_timestamps(local_audio_path)
        if not words_data:
            raise Exception("Transcription returned empty or failed.")
            
        # [NEW] 4. Predict Visual Hooks (B-Rolls Only)
        logger.info("Predicting Visual Hooks via Gemini")
        try:
            from features.visual_hooks.predictor import predict_visual_hooks
            from features.visual_hooks.fetcher import download_pexels_video
            hooks_data = predict_visual_hooks(words_data)
            
            downloaded_hooks = []
            if hooks_data:
                for i, hook in enumerate(hooks_data):
                    time_sec = hook.get("time")
                    
                    if time_sec is not None and hook.get("type") == "b_roll" and hook.get("search_query"):
                        video_path = os.path.join(temp_dir, f"hook_{i}.mp4")
                        if download_pexels_video(hook.get("search_query"), video_path):
                            downloaded_hooks.append({
                                "time": time_sec,
                                "type": "video",
                                "path": video_path
                            })
        except Exception as hooks_err:
            logger.error(f"Failed to generate visual hooks: {hooks_err}")
            downloaded_hooks = []
            
        # 5. Generate ASS Subtitle File
        logger.info("Generating ASS layout")
        ffu.generate_ass_file(words_data, local_ass_path, template_name)
        
        # 6. Burn Subtitles and Composited Assets via FFmpeg
        logger.info("Burning subtitles and overlays into video via FFmpeg")
        success = ffu.burn_subtitles_and_assets(local_video_path, local_ass_path, downloaded_hooks, local_output_path)
        if not success:
            raise Exception("Failed to burn subtitles with FFmpeg.")
            
        # 6. Upload Result to Supabase Storage
        logger.info("Uploading final video to Supabase Storage")
        unique_filename = f"captioned_{project_id}.mp4"
        with open(local_output_path, 'rb') as f:
            supabase.storage.from_('temporary-audio').upload(
                file=f.read(),
                path=unique_filename,
                file_options={"content-type": "video/mp4"}
            )
            
        public_output_url = supabase.storage.from_('temporary-audio').get_public_url(unique_filename)
        
        # 7. Update DB Status
        logger.info("Finalizing database record")
        supabase.table("projects").update({
            "status": "completed",
            "output_url": public_output_url,
            "transcript_json": words_data
        }).eq("id", project_id).execute()
        
        logger.info(f"Successfully finished project {project_id}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Failed to process video {project_id}: {e}")
        try:
            supabase.table("projects").update({
                "status": "failed",
                "output_url": None
            }).eq("id", project_id).execute()
        except Exception as update_err:
            logger.error(f"Failed to update error status in DB: {update_err}")
    finally:
        # Cleanup temp directory
        for file in os.listdir(temp_dir):
            try:
                os.remove(os.path.join(temp_dir, file))
            except:
                pass
        try:
            os.rmdir(temp_dir)
        except:
            pass
