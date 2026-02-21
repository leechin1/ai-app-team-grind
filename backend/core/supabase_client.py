"""
Supabase client and database operations
"""
import os
from typing import List, Optional, Dict, Any
from supabase import create_client, Client

from core.db_models import (
    Project, ProjectCreate,
    Note, NoteCreate, NoteUpdate,
    Document, DocumentCreate,
    FlashcardDB, FlashcardCreate, FlashcardReview, FlashcardReviewCreate,
    ChatMessage, ChatMessageCreate,
    Embedding, EmbeddingCreate,
    QuizQuestion, QuizQuestionCreate,
    MatchPair, MatchPairCreate
)


class SupabaseService:
    """Service for Supabase database operations"""

    def __init__(self):
        """Initialize Supabase client"""
        supabase_url = os.getenv("SUPABASE_URL")

        # Use SERVICE_KEY for development to bypass RLS, ANON_KEY for production
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("Missing Supabase credentials in .env file")

        self.client: Client = create_client(supabase_url, supabase_key)

    # ============================================
    # PROJECT OPERATIONS
    # ============================================

    async def create_project(self, user_id: str, project: ProjectCreate) -> Project:
        """Create a new project"""
        data = {
            "user_id": user_id,
            "name": project.name,
            "description": project.description,
            "icon": project.icon,
            "color": project.color
        }
        result = self.client.table("projects").insert(data).execute()
        return Project(**result.data[0])

    async def get_user_projects(self, user_id: str) -> List[Project]:
        """Get all projects for a user"""
        result = self.client.table("projects").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return [Project(**item) for item in result.data]

    async def get_project(self, project_id: str, user_id: str) -> Optional[Project]:
        """Get a specific project"""
        result = self.client.table("projects").select("*").eq("id", project_id).eq("user_id", user_id).execute()
        return Project(**result.data[0]) if result.data else None

    # ============================================
    # NOTE OPERATIONS
    # ============================================

    async def create_note(self, user_id: str, note: NoteCreate) -> Note:
        """Create a new note"""
        data = {
            "project_id": note.project_id,
            "user_id": user_id,
            "title": note.title,
            "content": note.content,
            "content_html": note.content_html,
            "course": note.course,
            "due_date": note.due_date,
            "type": note.type
        }
        result = self.client.table("notes").insert(data).execute()
        return Note(**result.data[0])

    async def get_project_notes(self, project_id: str, user_id: str) -> List[Note]:
        """Get all notes for a project"""
        result = self.client.table("notes").select("*").eq("project_id", project_id).eq("user_id", user_id).order("updated_at", desc=True).execute()
        return [Note(**item) for item in result.data]

    async def get_note(self, note_id: str, user_id: str) -> Optional[Note]:
        """Get a specific note"""
        result = self.client.table("notes").select("*").eq("id", note_id).eq("user_id", user_id).execute()
        return Note(**result.data[0]) if result.data else None

    async def update_note(self, note_id: str, user_id: str, update: NoteUpdate) -> Optional[Note]:
        """Update a note"""
        data = {k: v for k, v in update.dict(exclude_unset=True).items() if v is not None}
        if not data:
            return await self.get_note(note_id, user_id)
        result = self.client.table("notes").update(data).eq("id", note_id).eq("user_id", user_id).execute()
        return Note(**result.data[0]) if result.data else None

    # ============================================
    # DOCUMENT OPERATIONS
    # ============================================

    async def create_document(self, user_id: str, document: DocumentCreate) -> Document:
        """Create a new document record"""
        data = {
            "project_id": document.project_id,
            "user_id": user_id,
            "filename": document.filename,
            "file_path": document.file_path,
            "file_size": document.file_size,
            "mime_type": document.mime_type,
            "extracted_text": document.extracted_text,
            "page_count": document.page_count
        }
        result = self.client.table("documents").insert(data).execute()
        return Document(**result.data[0])

    async def get_project_documents(self, project_id: str, user_id: str) -> List[Document]:
        """Get all documents for a project"""
        result = self.client.table("documents").select("*").eq("project_id", project_id).eq("user_id", user_id).order("created_at", desc=True).execute()
        return [Document(**item) for item in result.data]

    async def get_document(self, document_id: str, user_id: str) -> Optional[Document]:
        """Get a specific document"""
        result = self.client.table("documents").select("*").eq("id", document_id).eq("user_id", user_id).execute()
        return Document(**result.data[0]) if result.data else None

    # ============================================
    # FLASHCARD OPERATIONS
    # ============================================

    async def create_flashcard(self, user_id: str, flashcard: FlashcardCreate) -> FlashcardDB:
        """Create a new flashcard"""
        data = {
            "project_id": flashcard.project_id,
            "user_id": user_id,
            "front": flashcard.front,
            "back": flashcard.back,
            "source_type": flashcard.source_type,
            "source_id": flashcard.source_id,
            "source_name": flashcard.source_name,
            "tags": flashcard.tags or [],
            "difficulty": flashcard.difficulty
        }
        result = self.client.table("flashcards").insert(data).execute()
        return FlashcardDB(**result.data[0])

    async def get_project_flashcards(self, project_id: str, user_id: str) -> List[FlashcardDB]:
        """Get all flashcards for a project"""
        result = self.client.table("flashcards").select("*").eq("project_id", project_id).eq("user_id", user_id).order("created_at", desc=True).execute()
        return [FlashcardDB(**item) for item in result.data]

    async def get_due_flashcards(self, project_id: str, user_id: str, limit: int = 20) -> List[FlashcardDB]:
        """Get flashcards due for review"""
        result = self.client.rpc(
            "get_due_flashcards",
            {"p_project_id": project_id, "p_user_id": user_id, "p_limit": limit}
        ).execute()
        return [FlashcardDB(**item) for item in result.data]

    async def get_flashcard(self, flashcard_id: str, user_id: str) -> Optional[FlashcardDB]:
        """Get a specific flashcard"""
        result = self.client.table("flashcards").select("*").eq("id", flashcard_id).eq("user_id", user_id).execute()
        return FlashcardDB(**result.data[0]) if result.data else None

    async def update_flashcard(self, flashcard_id: str, user_id: str, data: dict) -> Optional[FlashcardDB]:
        """Update a flashcard"""
        result = self.client.table("flashcards").update(data).eq("id", flashcard_id).eq("user_id", user_id).execute()
        return FlashcardDB(**result.data[0]) if result.data else None

    async def create_flashcard_review(self, user_id: str, review: FlashcardReviewCreate, flashcard_state: dict) -> FlashcardReview:
        """Create a flashcard review record"""
        data = {
            "flashcard_id": review.flashcard_id,
            "user_id": user_id,
            "quality": review.quality,
            "time_taken_seconds": review.time_taken_seconds,
            "easiness_factor": flashcard_state["easiness_factor"],
            "interval": flashcard_state["interval"],
            "repetitions": flashcard_state["repetitions"]
        }
        result = self.client.table("flashcard_reviews").insert(data).execute()
        return FlashcardReview(**result.data[0])

    # ============================================
    # CHAT MESSAGE OPERATIONS
    # ============================================

    async def create_chat_message(self, user_id: str, message: ChatMessageCreate) -> ChatMessage:
        """Create a chat message"""
        data = {
            "project_id": message.project_id,
            "user_id": user_id,
            "role": message.role,
            "content": message.content,
            "context_sources": message.context_sources or [],
            "prompt_tokens": message.prompt_tokens,
            "completion_tokens": message.completion_tokens
        }
        result = self.client.table("chat_messages").insert(data).execute()
        return ChatMessage(**result.data[0])

    async def get_project_chat_history(self, project_id: str, user_id: str, limit: int = 50) -> List[ChatMessage]:
        """Get chat history for a project"""
        result = self.client.table("chat_messages").select("*").eq("project_id", project_id).eq("user_id", user_id).order("created_at", desc=False).limit(limit).execute()
        return [ChatMessage(**item) for item in result.data]

    # ============================================
    # EMBEDDING OPERATIONS (RAG)
    # ============================================

    async def create_embedding(self, user_id: str, embedding: EmbeddingCreate) -> Embedding:
        """Create a vector embedding"""
        data = {
            "project_id": embedding.project_id,
            "user_id": user_id,
            "source_type": embedding.source_type,
            "source_id": embedding.source_id,
            "content": embedding.content,
            "chunk_index": embedding.chunk_index,
            "embedding": embedding.embedding,
            "metadata": embedding.metadata or {}
        }
        result = self.client.table("embeddings").insert(data).execute()
        return Embedding(**result.data[0])

    async def search_embeddings(
        self,
        project_id: str,
        query_embedding: List[float],
        threshold: float = 0.7,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar content using vector similarity"""
        result = self.client.rpc(
            "match_embeddings",
            {
                "query_embedding": query_embedding,
                "match_project_id": project_id,
                "match_threshold": threshold,
                "match_count": limit
            }
        ).execute()
        return result.data

    async def delete_source_embeddings(self, source_id: str, user_id: str) -> bool:
        """Delete all embeddings for a source"""
        result = self.client.table("embeddings").delete().eq("source_id", source_id).eq("user_id", user_id).execute()
        return len(result.data) > 0

    # ============================================
    # QUIZ QUESTION OPERATIONS
    # ============================================

    async def create_quiz_question(self, user_id: str, question: QuizQuestionCreate) -> QuizQuestion:
        """Create a new quiz question"""
        data = {
            "project_id": question.project_id,
            "user_id": user_id,
            "source_type": question.source_type,
            "source_id": question.source_id,
            "source_name": question.source_name,
            "question": question.question,
            "options": question.options,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "difficulty": question.difficulty
        }
        result = self.client.table("quiz_questions").insert(data).execute()
        return QuizQuestion(**result.data[0])

    async def get_project_quiz_questions(self, project_id: str, user_id: str) -> List[QuizQuestion]:
        """Get all quiz questions for a project"""
        result = self.client.table("quiz_questions").select("*").eq("project_id", project_id).eq("user_id", user_id).execute()
        return [QuizQuestion(**q) for q in result.data]

    async def delete_quiz_question(self, question_id: str, user_id: str) -> bool:
        """Delete a quiz question"""
        result = self.client.table("quiz_questions").delete().eq("id", question_id).eq("user_id", user_id).execute()
        return len(result.data) > 0

    # ============================================
    # MATCH PAIR OPERATIONS
    # ============================================

    async def create_match_pair(self, user_id: str, pair: MatchPairCreate) -> MatchPair:
        """Create a new match pair"""
        data = {
            "project_id": pair.project_id,
            "user_id": user_id,
            "source_type": pair.source_type,
            "source_id": pair.source_id,
            "source_name": pair.source_name,
            "term": pair.term,
            "definition": pair.definition
        }
        result = self.client.table("match_pairs").insert(data).execute()
        return MatchPair(**result.data[0])

    async def get_project_match_pairs(self, project_id: str, user_id: str) -> List[MatchPair]:
        """Get all match pairs for a project"""
        result = self.client.table("match_pairs").select("*").eq("project_id", project_id).eq("user_id", user_id).execute()
        return [MatchPair(**p) for p in result.data]

    async def delete_match_pair(self, pair_id: str, user_id: str) -> bool:
        """Delete a match pair"""
        result = self.client.table("match_pairs").delete().eq("id", pair_id).eq("user_id", user_id).execute()
        return len(result.data) > 0

    # ============================================
    # STUDY STATS OPERATIONS
    # ============================================

    async def get_project_flashcard_reviews(self, project_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get all flashcard reviews for a project (joining flashcards to filter by project)"""
        # Get flashcard IDs for this project
        flashcards_result = self.client.table("flashcards").select("id").eq("project_id", project_id).eq("user_id", user_id).execute()
        if not flashcards_result.data:
            return []

        flashcard_ids = [fc["id"] for fc in flashcards_result.data]

        # Get reviews for those flashcards
        reviews = []
        for fc_id in flashcard_ids:
            result = self.client.table("flashcard_reviews").select("*").eq("flashcard_id", fc_id).eq("user_id", user_id).execute()
            reviews.extend(result.data)

        return reviews

    async def get_project_stats_counts(self, project_id: str, user_id: str) -> Dict[str, int]:
        """Get counts of flashcards, quiz questions, and match pairs for a project"""
        flashcards = self.client.table("flashcards").select("id", count="exact").eq("project_id", project_id).eq("user_id", user_id).execute()
        quiz_questions = self.client.table("quiz_questions").select("id", count="exact").eq("project_id", project_id).eq("user_id", user_id).execute()
        match_pairs = self.client.table("match_pairs").select("id", count="exact").eq("project_id", project_id).eq("user_id", user_id).execute()
        documents = self.client.table("documents").select("id", count="exact").eq("project_id", project_id).eq("user_id", user_id).execute()
        notes = self.client.table("notes").select("id", count="exact").eq("project_id", project_id).eq("user_id", user_id).execute()

        return {
            "total_flashcards": flashcards.count if flashcards.count is not None else len(flashcards.data),
            "total_quiz_questions": quiz_questions.count if quiz_questions.count is not None else len(quiz_questions.data),
            "total_match_pairs": match_pairs.count if match_pairs.count is not None else len(match_pairs.data),
            "total_documents": documents.count if documents.count is not None else len(documents.data),
            "total_notes": notes.count if notes.count is not None else len(notes.data),
        }


# Global instance
db = SupabaseService()
