import google.generativeai as genai
import json
from .env import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro',
                              generation_config={"response_mime_type": "application/json"}) # type: ignore

async def episode_detection(filenames: list[str]) -> dict[str, int]: 
    prompt = f"""For these filenames: ```{json.dumps(filenames, ensure_ascii=True)}```, 
Please provide the episode number for each file. 
If you don't know the episode number, you can skip it. 
Output in json dict which the key is the filename and the value is the episode number in integer."""
    response = model.generate_content(prompt, safety_settings=[
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}
    ])
    return json.loads(response.text) # type: ignore