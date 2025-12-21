from pydantic import BaseModel
from typing import List, Optional, Any

class NoteCreate(BaseModel):
    title: str
    content: str
    user_id: str
    folder_id: Optional[str] = None

class NoteResponse(BaseModel):
    id: str
    title: str
    content: str
    structured_content: Optional[str] = None
    created_at: str

class StructureNoteRequest(BaseModel):
    note_id: str
    content: str

class Flashcard(BaseModel):
    question: str
    answer: str
    type: str = "basic"

class FlashcardResponse(BaseModel):
    flashcards: List[Flashcard]

class ChatRequest(BaseModel):
    message: str
    current_note_content: Optional[str] = None
    note_id: Optional[str] = None
    file_uri: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    updated_note_content: Optional[str] = None
