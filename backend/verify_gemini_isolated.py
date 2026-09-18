import os
import sys
from dotenv import load_dotenv

# Ensure we load the environment variables
backend_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(backend_dir, ".env"))
load_dotenv(os.path.join(os.path.dirname(backend_dir), ".env"))

api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key present: {bool(api_key)}")
if api_key:
    masked = api_key[:6] + "..." + api_key[-4:]
    print(f"API Key masked: {masked}")

from google import genai
from google.genai import types

print("Initializing genai.Client...")
client = genai.Client(api_key=api_key)

model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
print(f"Testing direct minimal call with model: {model_name}...")

try:
    response = client.models.generate_content(
        model=model_name,
        contents="Say 'Gemini connectivity verified' and nothing else.",
    )
    print("Direct Gemini SDK call SUCCESS!")
    print(f"Response text: {response.text.strip()}")
except Exception as e:
    print(f"Direct Gemini SDK call FAILED: {type(e).__name__}: {e}")
    sys.exit(1)
