import os
import subprocess
import logging

logger = logging.getLogger(__name__)

FFMPEG_CMD = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg" if os.path.exists("/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg") else "ffmpeg"

# Basic Templates mapped to ASS styles
TEMPLATES = {
    "viral_bold": {
        "Name": "ViralBold",
        "Fontname": "Arial",
        "Fontsize": "100",             # Scaled for 1080x1920
        "PrimaryColour": "&H00FFFFFF", # Base text is White
        "ActiveColour": "&H002BEE6C",  # Highlighted text is your brand Green
        "OutlineColour": "&H00000000",
        "BackColour": "&H80000000",
        "Bold": "-1",                 # Bold enabled
        "Italic": "0",
        "Outline": "8",
        "Shadow": "4",
        "Alignment": "2",             # bottom center
        "MarginL": "40",
        "MarginR": "40",
        "MarginV": "250"              # High enough over TikTok/Reel UI
    },
    "minimal": {
        "Name": "Minimal",
        "Fontname": "Helvetica",
        "Fontsize": "75",             # Scaled for 1080x1920
        "PrimaryColour": "&H00FFFFFF", 
        "ActiveColour": "&H0000FFFF",  # Highlighted text is Yellow
        "OutlineColour": "&H00000000",
        "BackColour": "&H00000000",
        "Bold": "0",
        "Italic": "0",
        "Outline": "4",
        "Shadow": "0",
        "Alignment": "2",
        "MarginL": "40",
        "MarginR": "40",
        "MarginV": "200"
    }
}

def extract_audio(video_path: str, output_audio_path: str) -> bool:
    """
    Extracts 16kHz mono audio from a video file suitable for Speech-to-Text.
    """
    cmd = [
        FFMPEG_CMD, "-y", "-i", video_path, 
        "-vn", "-acodec", "pcm_s16le", 
        "-ar", "16000", "-ac", "1", 
        output_audio_path
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg audio extraction failed: {e.stderr.decode('utf-8')}")
        return False

def format_time_ass(seconds: float) -> str:
    """Format seconds into ASS timestamp format: H:MM:SS.cs (centiseconds)"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    # centiseconds are 2 digits
    cs = int(round((seconds - int(seconds)) * 100))
    if cs == 100:
        cs = 99
    return f"{hrs}:{mins:02d}:{secs:02d}.{cs:02d}"

def generate_ass_file(words_data: list, output_ass_path: str, template_name: str = "viral_bold"):
    """
    Takes a list of word dictionaries (text, start, end) and writes a high-res ASS file.
    Creates Hormozi-style Word Animations: chunks words into a sentence, and generates individual
    dialogues showing the active word with styling (color and pop-out scale).
    """
    style = TEMPLATES.get(template_name, TEMPLATES["viral_bold"])
    
    # 1080x1920 for maximum clarity on TikTok/Shorts vertical aspect ratio
    ass_header = f"""[Script Info]
ScriptType: v4.00+
Collisions: Normal
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: {style["Name"]},{style["Fontname"]},{style["Fontsize"]},{style["PrimaryColour"]},&H000000FF,{style["OutlineColour"]},{style["BackColour"]},{style["Bold"]},{style["Italic"]},0,0,100,100,0,0,1,{style["Outline"]},{style["Shadow"]},{style["Alignment"]},{style["MarginL"]},{style["MarginR"]},{style["MarginV"]},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    lines = []
    chunk_size = 4  # Number of words to keep on screen at once
    
    for i in range(0, len(words_data), chunk_size):
        chunk = words_data[i:i+chunk_size]
        if not chunk: continue
        
        # Iterate over each word in the chunk to make it the 'active' word
        for j, active_word in enumerate(chunk):
            start_fmt = format_time_ass(active_word['start'])
            
            # The word stays highlighted until the next word starts, or until the end if it's the last word
            if j < len(chunk) - 1:
                end_fmt = format_time_ass(chunk[j+1]['start'])
            else:
                end_fmt = format_time_ass(active_word['end'])

            formatted_words = []
            for k, w in enumerate(chunk):
                if k == j:
                    # Active Word: color override + scale up (e.g. 115%), then {\r} to reset
                    formatted_words.append(f"{{\\c{style['ActiveColour']}\\fscx115\\fscy115}}{w['word'].strip()}{{\\r}}")
                else:
                    # Inactive Word: Base style (White)
                    formatted_words.append(w['word'].strip())
            
            dialogue_text = " ".join(formatted_words)
            lines.append(f"Dialogue: 0,{start_fmt},{end_fmt},{style['Name']},,0,0,0,,{dialogue_text}")

    with open(output_ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header)
        for line in lines:
            f.write(line + "\n")

    return True

def burn_subtitles_and_assets(video_path: str, ass_path: str, hooks: list, output_video_path: str) -> bool:
    """
    Burns the generated ASS file and composites dynamically downloaded video assets onto the main video.
    """
    work_dir = os.path.dirname(output_video_path)
    video_file = os.path.basename(video_path)
    ass_file = os.path.basename(ass_path)
    output_file = os.path.basename(output_video_path)
    
    cmd = [FFMPEG_CMD, "-y", "-i", video_file]
    
    for hook in hooks:
        if hook.get("type") == "video":
            cmd.extend(["-i", os.path.basename(hook["path"])])
        
    if hooks:
        filter_complex = ""
        last_out = "0:v"
        
        for i, hook in enumerate(hooks):
            if hook.get("type") == "video":
                start_time = float(hook["time"])
                end_time = start_time + 1.5
                
                img_index = i + 1
                current_out = f"v{i+1}"
                
                prep_out = f"prep{i}"
                filter_complex += f"[{img_index}:v]setpts=PTS-STARTPTS+{start_time}/TB,scale=600:-1,format=rgba[{prep_out}];"
                overlay_str = f"[{last_out}][{prep_out}]overlay=x=(W-w)/2:y=(H-h)/6:eof_action=pass:enable='between(t,{start_time},{end_time})'[{current_out}];"
                    
                filter_complex += overlay_str
                last_out = current_out
            
        filter_complex += f"[{last_out}]subtitles={ass_file}[vout]"
        
        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-map", "0:a"
        ])
    else:
        # Fallback to simple video filter if no hooks
        cmd.extend([
            "-vf", f"subtitles={ass_file}"
        ])
        
    cmd.extend([
        "-c:v", "libx264", "-c:a", "copy",
        output_file
    ])
    
    try:
        subprocess.run(cmd, cwd=work_dir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg subtitle and overlay compositing failed: {e.stderr.decode('utf-8')}")
        return False
