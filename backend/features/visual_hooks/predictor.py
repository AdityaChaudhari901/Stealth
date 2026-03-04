import json
from google import genai
from google.genai import types

# Configure Gemini Client
client = genai.Client()

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
    
    Choose 2-4 high-impact moments. For each moment, provide a 1-2 word search query for a stock video (e.g., 'money falling', 'rocket launch') that visually complements the audio.
    
    Output strictly as a JSON list of objects:
    [
      {{"time": 5.4, "type": "b_roll", "search_query": "office working"}},
      {{"time": 12.1, "type": "b_roll", "search_query": "stock chart up"}}
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
