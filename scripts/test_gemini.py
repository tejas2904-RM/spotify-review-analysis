"""Quick sanity-check: verifies the Gemini API key works and returns valid JSON."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.ai.llm import call, load_cache, _provider

print(f"Active provider: {_provider()}")
load_cache()
result = call(
    system="You are a JSON API. Always respond with valid JSON only.",
    user='Respond with {"status": "ok", "message": "Gemini is working"}',
    max_tokens=60,
)
print("Result:", result)
if result.get("status") == "ok":
    print("\nGemini integration is working correctly.")
else:
    print("\nUnexpected response — check the output above.")
