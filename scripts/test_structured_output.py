import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.models import FlashCard 
from core.ai_generator import AIContentGenerator
from pydantic import TypeAdapter
from google import genai 
from dotenv import load_dotenv 
import json
import os 

load_dotenv()

schema = TypeAdapter(FlashCard).json_schema()

print(json.dumps(schema, indent= 2))

prompt = """
          Cria um flash card sobre o que é a mitocondria.              
         """


client = genai.Client(api_key = os.getenv('GEMINI_API_KEY'))

response = client.models.generate_content(
    model = "gemini-2.5-flash",
    contents = prompt,
    config = {"response_mime_type": "application/json",
              "response_schema": schema
    }
)

print(response.text)                        