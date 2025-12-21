from google import genai
from google.genai import types
from ..config import settings

class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def structure_note(self, content: str) -> str:
        prompt = f"""
        You are Notiq's note structuring AI. Transform the raw notes into a well-structured, study-friendly format.
        
        Raw note content:
        {content}
        
        Structure the note with:
        1. Clear hierarchical headings
        2. Bullet points for lists
        3. **Bold** for key terms and concepts
        4. Summary section at the end
        
        Return only the structured markdown content.
        """
        
        response = self.client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[
                types.Content(
                    role='user',
                parts=[types.Part.from_text(text=prompt)]
                )
            ]
        )
        return response.text

    def upload_file(self, file_content: bytes, mime_type: str) -> str:
        import tempfile
        import os
        
        # Save bytes to a temporary file
        suffix = ".pdf" if mime_type == "application/pdf" else ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name
            
        try:
            # Upload to Gemini
            # Note: The SDK might be client.files.upload or similar. 
            # We are using google.genai.Client.
            # Based on standard usage:
            file_obj = self.client.files.upload(path=tmp_path, config=types.UploadFileConfig(mime_type=mime_type))
            return file_obj.uri
        except Exception as e:
            print(f"Gemini Upload Error: {e}")
            raise e
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def chat_with_note(self, message: str, note_content: str | None, file_uri: str | None = None) -> dict:
        prompt_text = f"""
        You are an intelligent note-taking assistant.
        
        User Message: "{message}"
        
        Current Note Content (if any):
        {note_content if note_content else "No note selected."}
        
        Your Goal:
        1. Answer the user's question or follow their instruction.
        2. If the user asks to modify, summarize, or add to the note, provide the COMPLETE updated content of the note. For example if the user asks to add a sentence, return the whole previous note plus the new sentence.
        
        Output Format (JSON):
        {{
            "reply": "Your conversational response to the user",
            "updated_note_content": "The full updated note content (only if changed, otherwise null)"
        }}
        """
        
        try:
            if file_uri:
                # If we have a file, we pass it as a Part
                parts = [
                    types.Part.from_uri(file_uri=file_uri, mime_type='application/pdf'),
                    types.Part.from_text(text=prompt_text)
                ]
            else:
                parts = [types.Part.from_text(text=prompt_text)]

            response = self.client.models.generate_content(
                model='gemini-2.0-flash',
                contents=[
                    types.Content(
                        role='user',
                        parts=parts
                    )
                ],
                config=types.GenerateContentConfig(
                    response_mime_type='application/json'
                )
            )
            import json
            return json.loads(response.text)
        except Exception as e:
            print(f"Gemini Chat Error: {e}")
            return {
                "reply": f"I'm sorry, I encountered an error processing your request: {str(e)}",
                "updated_note_content": None
            }

gemini_service = GeminiService()
