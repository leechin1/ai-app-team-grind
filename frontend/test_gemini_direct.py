import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key present: {bool(api_key)}")

client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=[
            types.Content(
                role='user',
                parts=[types.Part.from_text(text="Say hello")]
            )
        ]
    )
    print("Gemini Response:", response.text)
except Exception as e:
    print(f"Gemini Error: {e}")
