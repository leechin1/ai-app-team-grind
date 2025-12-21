from fastapi import FastAPI
from .models import schemas
from .models.schemas import StructureNoteRequest
from .services.gemini import gemini_service
from .services.supabase import supabase_service

app = FastAPI(title="Notiq API")

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Notiq API is running"}
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from .services.gemini import gemini_service
from .models import schemas
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/structure")
def structure_note(request: schemas.NoteRequest):
    structured_content = gemini_service.structure_note(request.content)
    return {"structured_content": structured_content}

@app.post("/api/chat")
def chat(request: schemas.ChatRequest):
    response = gemini_service.chat_with_note(request.message, request.current_note_content, request.file_uri)
    return response

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        # file.content_type should be 'application/pdf'
        file_uri = gemini_service.upload_file(content, file.content_type or "application/pdf")
        return {
            "id": str(uuid.uuid4()),
            "name": file.filename,
            "file_uri": file_uri,
            "type": "pdf"
        }
    except Exception as e:
        return {"error": str(e)}

# Allow Vercel to handle the entry point
# No "if __name__ == '__main__':" needed for Vercel, but useful for local dev
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
