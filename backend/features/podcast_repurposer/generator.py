import os
import json
from google import genai
from google.genai import types

# Configure Gemini Client
client = genai.Client()

def generate_hooks(transcript: str, count: int = 10) -> list:
    """
    Extracts the highest-retention moments and scores them.
    """
    prompt = f"""
    You are an expert social media growth hacker. I am going to provide you with a transcript from a podcast.
    Extract the {count} most compelling, controversial, highly-specific, or emotionally triggering concepts discussed. 
    
    For each concept, write a 'Viral Hook' (1-2 sentences) designed to stop someone scrolling on TikTok/Reels/Shorts. 
    Next to each hook, provide a 'score' out of 100 based on Curiosity, Clarity, and Emotional Pull.
    Also provide a short 'reason' for why this hook scores highly.
    
    Output strictly as a JSON list of objects with the following keys:
    [
      {{"hook": "string", "score": 90, "reason": "string"}}
    ]
    
    Transcript:
    {transcript}
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.7,
        ),
    )
    
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        print("Failed to decode JSON from Gemini response:", response.text)
        return []

def generate_scripts(hooks: list, transcript: str) -> list:
    """
    Takes top viral hooks and generates 30-60sec short-form scripts.
    """
    # Only pick the top 5 hooks for the scripts
    top_hooks = sorted(hooks, key=lambda x: x.get('score', 0), reverse=True)[:5]
    hooks_text = json.dumps([h['hook'] for h in top_hooks], indent=2)
    
    prompt = f"""
    You are a master short-form video scriptwriter. 
    Based on the overall transcript provided and the {len(top_hooks)} specific hooks below, 
    write a complete 30-60 second short-form video script for each hook.
    
    Structure each script EXACTLY with these 3 keys:
    1. "hook": the exact hook provided.
    2. "body": Condense the podcaster's actual point into 3-4 punchy, conversational sentences. Keep the exact value/lesson intact. Add visual cues in brackets like [PAUSE].
    3. "cta": A strong Call to Action (e.g., 'Listen to the full episode at the link in bio').
    
    Output strictly as a JSON list of objects with the keys: "hook", "body", "cta".
    
    Hooks:
    {hooks_text}
    
    Transcript:
    {transcript}
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.7,
        ),
    )
    
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        print("Failed to decode JSON from Gemini response:", response.text)
        return []

def generate_social_posts(transcript: str) -> dict:
    """
    Generates LinkedIn posts, Tweets, and Captions.
    """
    prompt = f"""
    You are an expert social media manager. Based on the following podcast transcript, generate:
    
    1. "linkedin": 3 completely standalone, highly authoritative LinkedIn posts. Start with a strong single-sentence opening, use bullet points, and end with a question.
    2. "tweets": 5 standalone Twitter (X) tweets summarizing the best quotes or counter-intuitive points.
    3. "captions_short": 1 short caption for Youtube Shorts / TikTok. Highly curiosity driven.
    4. "captions_long": 1 long-form caption for Instagram summarizing the entire episode.
    5. "hashtags": A list of 10 highly relevant hashtags.
    
    Output strictly as a JSON object with these exact keys:
    {{
      "linkedin": ["string", "string", "string"],
      "tweets": ["string", "string", "string", "string", "string"],
      "captions_short": "string",
      "captions_long": "string",
      "hashtags": ["string", "string"]
    }}
    
    Transcript:
    {transcript}
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.7,
        ),
    )
    
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        print("Failed to decode JSON from Gemini response:", response.text)
        return {}

def generate_show_notes(transcript: str) -> dict:
    """
    Generates YouTube/Spotify show notes with timestamps, titles, and a summary.
    """
    prompt = f"""
    You are an expert podcast manager and YouTube SEO specialist. Based on the following podcast transcript, generate:
    
    1. "titles": A list of 5 high-converting, click-worthy YouTube titles for this episode.
    2. "description": A formatted YouTube description (in markdown) that includes:
        - A compelling 2-3 paragraph summary optimized for SEO.
        - "Key Takeaways": A bulleted list of the top 3-5 lessons.
        - "Timestamps": A list of 5-7 crucial moments with estimated timestamps (format like 00:00). Since the raw text may lack exact timing, estimate the chronological flow if needed (e.g., 00:00 Intro, 05:30 First Topic, etc.).
    
    Output strictly as a JSON object with these exact keys:
    {{
      "titles": ["string", "string", "string"],
      "description": "string"
    }}
    
    Transcript:
    {transcript}
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.7,
        ),
    )
    
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        print("Failed to decode JSON from Gemini response:", response.text)
        return {"titles": [], "description": ""}

def generate_newsletter(transcript: str) -> dict:
    """
    Generates a highly-clickable email newsletter broadcast.
    """
    prompt = f"""
    You are an expert email marketer specializing in creator newsletters. Based on the following podcast transcript, write an engaging, high-converting weekly email broadcast.
    
    The goal is to get subscribers to click on the link to watch/listen to the full episode. 
    Use a conversational, punchy tone. Structure it well with short paragraphs.
    
    Output strictly as a JSON object with these exact keys:
    {{
      "subject": "A highly clickable email subject line",
      "body": "The full email body formatted in markdown. Include placeholders like [Link to Episode] where appropriate."
    }}
    
    Transcript:
    {transcript}
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.7,
        ),
    )
    
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        print("Failed to decode JSON from Gemini response:", response.text)
        return {"subject": "", "body": ""}

def predict_visual_hooks(words_data: list) -> list:
    """
    Analyzes word-level timestamped data to predict high-impact emoji placements.
    Returns a list of dicts: [{"time": 1.2, "emoji": "🚀"}]
    """
    if not words_data:
        return []
        
    # Compress transcript into 5-word chunks with timestamps for Gemini context
    text_with_times = ""
    for i in range(0, len(words_data), 5):
        chunk = words_data[i:i+5]
        start = chunk[0]['start']
        text = " ".join([w['word'].strip() for w in chunk])
        text_with_times += f"[{start:.1f}s] {text}\n"

    prompt = f"""
    You are an expert short-form video editor (similar to Hormozi style).
    Analyze this timestamped transcript. Identify emotionally or conceptually significant moments (pattern interrupts, cognitive spikes, story tension points) that would benefit from visual reinforcement.
    
    Choose 2-4 high-impact moments. For each moment, pick ONE relevant Unicode emoji character (e.g., 🚀, 💰, 🤯, 💀, 🔥).
    
    Output strictly as a JSON list of objects:
    [
      {{"time": 1.2, "emoji": "🚀"}}
    ]
    
    Make sure the `time` closely matches the timestamp of the key word in the transcript.
    
    Transcript with timestamps:
    {text_with_times}
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.7,
        ),
    )
    
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        print("Failed to decode JSON from Gemini visual hook response:", response.text)
        return []
