import json
from pathlib import Path
import google.generativeai as genai

# Load API key from secrets.json
with open(Path("secrets.json"), "r") as f:
    secrets = json.load(f)
api_key = secrets.get("google_api_key") or secrets.get("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("Google API key not found in secrets.json!")
genai.configure(api_key=api_key)

print("Available Gemini models:")
for model in genai.list_models():
    print(f"- {model.name} (methods: {getattr(model, 'supported_generation_methods', 'N/A')})")

if __name__ == "__main__":
    list_gemini_models()

model = genai.GenerativeModel('models/gemini-2.0-flash-lite') 