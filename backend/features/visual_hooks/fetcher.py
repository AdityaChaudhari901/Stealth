import os
import requests
import logging

logger = logging.getLogger(__name__)



def download_pexels_video(query: str, output_path: str) -> bool:
    """
    Downloads the highest quality version of a Pexels stock video based on a search query.
    """
    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key:
        logger.error("PEXELS_API_KEY environment variable not set.")
        return False
        
    url = f"https://api.pexels.com/videos/search?query={query}&orientation=landscape&size=medium&per_page=1"
    headers = {"Authorization": api_key}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("videos"):
            logger.warning(f"No Pexels videos found for query: {query}")
            return False
            
        video_data = data["videos"][0]
        
        # Pexels provides multiple video files with different qualities. Pick the HD/highest one.
        video_files = video_data.get("video_files", [])
        if not video_files:
            return False
            
        # Sort by resolution (width * height), fallback to 0 if dimensions are missing
        video_files.sort(key=lambda x: (x.get("width", 0) * x.get("height", 0)), reverse=True)
        best_file_url = video_files[0].get("link")
        
        if not best_file_url:
            return False
            
        # Download the actual MP4 file
        vid_response = requests.get(best_file_url, stream=True)
        vid_response.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in vid_response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        logger.error(f"Failed to fetch Pexels video for query '{query}': {e}")
        return False
