"""
Database models matching Supabase schema
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid


# ============================================
# USER & PROJECT MODELS
# ============================================

class ProjectCreate(BaseModel):
    """Request to create a project"""
    name: str
    description: Optional[str] = None
    icon: Optional[str] = "📚"
    color: Optional[str] = "from-blue-500 to-cyan-600"


class Project(BaseModel):
    """Project model"""
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    icon: str = "📚"
    color: str = "from-blue-500 to-cyan-600"
    created_at: datetime
    updated_at: datetime


# ============================================
# NOTE MODELS
# ============================================

class NoteCreate(BaseModel):
    """Request to create a note"""
    project_id: str
    title: Optional[str] = "Untitled"
    content: Optional[str] = ""
    content_html: Optional[str] = ""
    course: Optional[str] = None
    due_date: Optional[str] = None
    type: Optional[str] = "Study Notes"


class NoteUpdate(BaseModel):
    """Request to update a note"""
    title: Optional[str] = None
    content: Optional[str] = None
    content_html: Optional[str] = None
    course: Optional[str] = None
    due_date: Optional[str] = None
    type: Optional[str] = None


class Note(BaseModel):
    """Note model"""
    id: str
    project_id: str
    user_id: str
    title: str
    content: str
    content_html: str
    course: Optional[str] = None
    due_date: Optional[str] = None
    type: str
    created_at: datetime
    updated_at: datetime


# ============================================
# DOCUMENT MODELS
# ============================================

class DocumentCreate(BaseModel):
    """Request to create a document"""
    project_id: str
    filename: str
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    extracted_text: Optional[str] = None
    page_count: Optional[int] = None


class Document(BaseModel):
    """Document model"""
    id: str
    project_id: str
    user_id: str
    filename: str
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    extracted_text: Optional[str] = None
    page_count: Optional[int] = None
    created_at: datetime


# ============================================
# FLASHCARD MODELS
# ============================================

class FlashcardCreate(BaseModel):
    """Request to create a flashcard"""
    project_id: str
    front: str
    back: str
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    source_name: Optional[str] = None
    tags: Optional[List[str]] = None
    difficulty: Optional[str] = "medium"


class FlashcardDB(BaseModel):
    """Flashcard from database"""
    id: str
    project_id: str
    user_id: str
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    source_name: Optional[str] = None
    front: str
    back: str
    easiness_factor: float = 2.5
    interval: int = 0
    repetitions: int = 0
    next_review_date: datetime
    last_review_date: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    difficulty: str = "medium"
    created_at: datetime
    updated_at: datetime


class FlashcardReviewCreate(BaseModel):
    """Request to create a review"""
    flashcard_id: str
    quality: int
    time_taken_seconds: Optional[int] = None


class FlashcardReview(BaseModel):
    """Flashcard review record"""
    id: str
    flashcard_id: str
    user_id: str
    quality: int
    time_taken_seconds: Optional[int] = None
    easiness_factor: float
    interval: int
    repetitions: int
    reviewed_at: datetime


# ============================================
# CHAT MESSAGE MODELS
# ============================================

class ChatMessageCreate(BaseModel):
    """Request to create a chat message"""
    project_id: str
    role: str
    content: str
    context_sources: Optional[List[dict]] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None


class ChatMessage(BaseModel):
    """Chat message"""
    id: str
    project_id: str
    user_id: str
    role: str
    content: str
    context_sources: List[dict] = Field(default_factory=list)
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    created_at: datetime


# ============================================
# EMBEDDING MODELS
# ============================================

class EmbeddingCreate(BaseModel):
    """Request to create an embedding"""
    project_id: str
    source_type: str
    source_id: str
    content: str
    chunk_index: int = 0
    embedding: List[float]
    metadata: Optional[dict] = None


class Embedding(BaseModel):
    """Vector embedding"""
    id: str
    project_id: str
    user_id: str
    source_type: str
    source_id: str
    content: str
    chunk_index: int = 0
    embedding: Optional[List[float]] = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime


# ============================================
# QUIZ QUESTION MODELS
# ============================================

class QuizQuestionCreate(BaseModel):
    """Request to create a quiz question"""
    project_id: str
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    source_name: Optional[str] = None
    question: str
    options: List[str]
    correct_answer: str
    explanation: Optional[str] = None
    difficulty: str = "medium"


class QuizQuestion(BaseModel):
    """Quiz question from database"""
    id: str
    project_id: str
    user_id: str
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    source_name: Optional[str] = None
    question: str
    options: List[str]
    correct_answer: str
    explanation: Optional[str] = None
    difficulty: str = "medium"
    created_at: datetime


# ============================================
# MATCH PAIR MODELS
# ============================================

class MatchPairCreate(BaseModel):
    """Request to create a match pair"""
    project_id: str
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    source_name: Optional[str] = None
    term: str
    definition: str


class MatchPair(BaseModel):
    """Match pair from database"""
    id: str
    project_id: str
    user_id: str
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    source_name: Optional[str] = None
    term: str
    definition: str
    created_at: datetime
