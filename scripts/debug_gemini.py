"""Debug raw Gemini API error without retry wrapper."""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv; load_dotenv()

from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
try:
    resp = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Reply with valid JSON only: {\"status\": \"ok\"}",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            max_output_tokens=50,
        ),
    )
    print("SUCCESS:", resp.text)
except Exception as e:
    print("RAW ERROR TYPE:", type(e).__name__)
    print("RAW ERROR:", str(e))
