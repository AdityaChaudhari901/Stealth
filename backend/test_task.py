import os
import sys
import uuid
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

# Add parent dir to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.video_renderer import process_video_task

def main():
    test_id = str(uuid.uuid4())
    print(f"Testing with dynamic UUID: {test_id}")
    # Using a slightly longer clip so there's enough dialogue to get good hooks
    process_video_task(test_id, "https://www.w3schools.com/html/mov_bbb.mp4", "viral_bold", "en")

if __name__ == "__main__":
    main()
