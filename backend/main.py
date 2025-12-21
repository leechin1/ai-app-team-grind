"""
FastAPI Backend for AI Study App.

Provides RESTful API endpoints for:
- Flashcard generation and review
- Quiz generation and submission
- Match quiz generation and submission
- Spaced repetition (SM-2)
- Analytics and statistics
"""

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
import uuid
from pathlib import Path

# Import core modules
from core.ai_generator import AIContentGenerator
from core.models import (
    FlashCard, FlashcardGenerationRequest, FlashcardGenerationResponse,
    QuizQuestion, QuizAnswer, QuizResult,
    MatchPair, MatchQuizGenerationResponse, MatchQuizAnswer, MatchQuizResult,
    ResponseQuality, DifficultyLevel
)
from core.spaced_repetition import SM2SpacedRepetition
from core.review_logger import UnifiedReviewLogger
from core.document_processor import DocumentProcessor


# ==================== FastAPI App Setup ====================

app = FastAPI(
    title="AI Study App API",
    description="Backend API for AI-powered study materials generation and spaced repetition",
    version="1.0.0"
)

# CORS middleware - Allow React frontend to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "http://localhost:8080",  # Vite dev server (alternative port)
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Global State ====================
# In production, use a database instead of in-memory storage

class AppState:
    """Global application state (in-memory for now)"""
    def __init__(self):
        self.flashcards: dict[str, FlashCard] = {}  # flashcard_id -> FlashCard
        self.active_quizzes: dict[str, List[QuizQuestion]] = {}  # quiz_id -> questions
        self.active_match_quizzes: dict[str, List[MatchPair]] = {}  # match_quiz_id -> pairs
        self.uploaded_documents: dict[str, dict] = {}  # doc_id -> {filename, content, uploaded_at}
        self.sm2 = SM2SpacedRepetition()
        self.logger = UnifiedReviewLogger()
        self.api_key = os.getenv("GEMINI_API_KEY")

state = AppState()


# ==================== Request/Response Models ====================

class ReviewFlashcardRequest(BaseModel):
    """Request to review a flashcard"""
    flashcard_id: str
    response_quality: int  # 0-5 scale
    was_correct: bool
    time_spent_seconds: float


class GenerateQuizRequest(BaseModel):
    """Request to generate a quiz"""
    content: str
    num_questions: int = 5
    difficulty: Optional[str] = "medium"
    focus_topics: Optional[List[str]] = None


class SubmitQuizRequest(BaseModel):
    """Request to submit quiz answers"""
    quiz_id: str
    answers: List[QuizAnswer]


class QuizGenerationResponse(BaseModel):
    """Response from quiz generation"""
    quiz_id: str
    questions: List[QuizQuestion]


class GenerateMatchQuizRequest(BaseModel):
    """Request to generate a match quiz"""
    content: str
    num_pairs: int = 5
    difficulty: Optional[str] = "medium"
    focus_topics: Optional[List[str]] = None


class SubmitMatchQuizRequest(BaseModel):
    """Request to submit match quiz answers"""
    match_quiz_id: str
    answers: List[MatchQuizAnswer]


class StructureNoteRequest(BaseModel):
    """Request to structure a note with AI"""
    note_id: str
    content: str


class ChatRequest(BaseModel):
    """Request to chat with AI"""
    message: str
    context: Optional[str] = None
    source_id: Optional[str] = None
    file_uri: Optional[str] = None


# ==================== Flashcard Endpoints ===================="

@app.post("/api/flashcards/generate", response_model=FlashcardGenerationResponse)
async def generate_flashcards(request: FlashcardGenerationRequest):
    """
    Generate flashcards from text content.

    Args:
        request: Content and generation parameters

    Returns:
        FlashcardGenerationResponse with generated flashcards
    """
    try:
        if not state.api_key:
            raise HTTPException(
                status_code=500,
                detail="Gemini API key not configured. Set GEMINI_API_KEY environment variable."
            )

        # Convert difficulty string to enum
        difficulty = DifficultyLevel(request.difficulty_filter) if request.difficulty_filter else None

        # Initialize AI generator
        generator = AIContentGenerator(api_key=state.api_key)

        # Generate flashcards
        response = generator.generate_flashcards(
            content=request.content,
            num_cards=request.num_cards,
            difficulty_filter=difficulty,
            focus_topics=None  # focus_topics not in FlashcardGenerationRequest model
        )

        # Store flashcards in memory
        for flashcard in response.flashcards:
            state.flashcards[flashcard.id] = flashcard

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate flashcards: {str(e)}")


@app.get("/api/flashcards/due")
async def get_due_flashcards():
    """
    Get flashcards that are due for review.

    Returns:
        List of FlashCard objects due for review
    """
    try:
        all_cards = list(state.flashcards.values())
        due_cards = state.sm2.get_due_cards(all_cards)

        return {
            "due_cards": [card.model_dump() for card in due_cards],
            "total_due": len(due_cards)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get due flashcards: {str(e)}")


@app.get("/api/flashcards/{flashcard_id}")
async def get_flashcard(flashcard_id: str):
    """Get a specific flashcard by ID"""
    if flashcard_id not in state.flashcards:
        raise HTTPException(status_code=404, detail="Flashcard not found")

    return state.flashcards[flashcard_id].model_dump()


@app.post("/api/flashcards/review")
async def review_flashcard(request: ReviewFlashcardRequest):
    """
    Submit a flashcard review.

    Args:
        request: Review details (flashcard_id, response_quality, etc.)

    Returns:
        Updated flashcard with new SM-2 parameters
    """
    try:
        # Get flashcard
        if request.flashcard_id not in state.flashcards:
            raise HTTPException(status_code=404, detail="Flashcard not found")

        card = state.flashcards[request.flashcard_id]

        # Process review with SM-2
        updated_card = state.sm2.process_review(
            card=card,
            response_quality=request.response_quality
        )

        # Log review interaction
        state.logger.log_flashcard_review(
            flashcard=updated_card,
            response_quality=request.response_quality,
            was_correct=request.was_correct,
            time_spent_seconds=request.time_spent_seconds
        )

        # Update in memory
        state.flashcards[request.flashcard_id] = updated_card

        # Get stats
        stats = state.sm2.get_review_stats(updated_card)

        return {
            "flashcard": updated_card.model_dump(),
            "stats": stats,
            "message": f"Next review in {stats['days_until_review']} days"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to review flashcard: {str(e)}")


# ==================== Quiz Endpoints ====================

@app.post("/api/quiz/generate", response_model=QuizGenerationResponse)
async def generate_quiz(request: GenerateQuizRequest):
    """
    Generate a quiz from text content.

    Args:
        request: Content and generation parameters

    Returns:
        QuizGenerationResponse with generated questions
    """
    try:
        # Convert difficulty string to enum
        difficulty = DifficultyLevel(request.difficulty) if request.difficulty else None

        # Initialize AI generator
        generator = AIContentGenerator(api_key=state.api_key)

        # Generate quiz questions
        questions = generator.generate_quiz(
            content=request.content,
            num_questions=request.num_questions,
            difficulty_filter=difficulty,
            focus_topics=request.focus_topics
        )

        # Generate unique quiz ID
        import uuid
        quiz_id = str(uuid.uuid4())

        # Store quiz in state for later submission validation
        state.active_quizzes[quiz_id] = questions

        return QuizGenerationResponse(quiz_id=quiz_id, questions=questions)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")


@app.post("/api/quiz/submit")
async def submit_quiz(request: SubmitQuizRequest):
    """
    Submit quiz answers and get results.

    Args:
        request: Quiz ID and user answers

    Returns:
        QuizResult with score and feedback
    """
    try:
        # In production, you'd load the quiz from database
        # For now, we'll just calculate the score from the answers

        # Here we need to match against the original questions
        # For simplicity, assuming the frontend sends complete answer data

        # Log quiz attempts as verified interactions
        for answer in request.answers:
            # Create a dummy flashcard ID for tag linking
            # In production, you'd link to actual flashcards via tags
            flashcard_id = f"quiz_{request.quiz_id}_{answer.question_id}"

            # Note: This is simplified - you'd need to pass the actual question
            # to extract tags properly. For now, we'll skip detailed logging.

        return {
            "quiz_id": request.quiz_id,
            "message": "Quiz submitted successfully",
            "note": "Detailed results require storing quiz questions"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit quiz: {str(e)}")


# ==================== Match Quiz Endpoints ====================

@app.post("/api/match/generate", response_model=MatchQuizGenerationResponse)
async def generate_match_quiz(request: GenerateMatchQuizRequest):
    """
    Generate a match quiz from stored flashcards or text content.

    Args:
        request: Generation parameters (if content is empty, uses existing flashcards)

    Returns:
        MatchQuizGenerationResponse with match pairs
    """
    try:
        # Check if user wants to use existing flashcards or generate from content
        if request.content and request.content.strip():
            # Generate new match pairs from content using AI
            if not state.api_key:
                raise HTTPException(
                    status_code=500,
                    detail="Gemini API key not configured. Set GEMINI_API_KEY environment variable."
                )

            difficulty = DifficultyLevel(request.difficulty) if request.difficulty else None
            generator = AIContentGenerator(api_key=state.api_key)

            response = generator.generate_match_quiz(
                content=request.content,
                num_pairs=request.num_pairs,
                difficulty_filter=difficulty,
                focus_topics=request.focus_topics
            )

            # Store match quiz
            quiz_id = str(uuid.uuid4())
            state.active_match_quizzes[quiz_id] = response.pairs

            return response
        else:
            # Use existing flashcards to create match pairs
            all_flashcards = list(state.flashcards.values())
            
            if not all_flashcards:
                raise HTTPException(
                    status_code=400,
                    detail="No flashcards available. Generate flashcards first or provide content."
                )

            # Filter by difficulty if specified
            if request.difficulty:
                difficulty = DifficultyLevel(request.difficulty)
                all_flashcards = [fc for fc in all_flashcards if fc.difficulty == difficulty]
                
            if not all_flashcards:
                raise HTTPException(
                    status_code=400,
                    detail=f"No flashcards found with difficulty: {request.difficulty}"
                )

            # Randomly select flashcards
            import random
            num_pairs = min(request.num_pairs or 5, len(all_flashcards))
            selected_flashcards = random.sample(all_flashcards, num_pairs)

            # Convert flashcards to match pairs
            pairs = [
                MatchPair(
                    id=fc.id,
                    prompt=fc.front,
                    answer=fc.back,
                    hint=None,
                    tags=fc.tags
                )
                for fc in selected_flashcards
            ]

            # Store match quiz
            quiz_id = str(uuid.uuid4())
            state.active_match_quizzes[quiz_id] = pairs

            return MatchQuizGenerationResponse(
                match_quiz_id=quiz_id,
                pairs=pairs,
                total_pairs=len(pairs),
                content_length=0,
                generation_time_seconds=0.0
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate match quiz: {str(e)}")


@app.post("/api/match/submit")
async def submit_match_quiz(request: SubmitMatchQuizRequest):
    """
    Submit match quiz answers and get results.

    Args:
        request: Match quiz ID and user answers

    Returns:
        Results with score
    """
    try:
        # Similar to quiz submission, this is simplified
        # In production, store and retrieve match pairs

        return {
            "match_quiz_id": request.match_quiz_id,
            "message": "Match quiz submitted successfully",
            "note": "Detailed results require storing match pairs"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit match quiz: {str(e)}")


# ==================== Analytics Endpoints ====================

@app.get("/api/stats")
async def get_statistics():
    """
    Get overall user statistics.

    Returns:
        Statistics about interactions, accuracy, ML readiness
    """
    try:
        stats = state.logger.get_statistics()

        # Add flashcard stats
        total_flashcards = len(state.flashcards)
        due_flashcards = len(state.sm2.get_due_cards(list(state.flashcards.values())))

        stats["flashcards"] = {
            "total": total_flashcards,
            "due": due_flashcards
        }

        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@app.get("/api/stats/ml-readiness")
async def check_ml_readiness():
    """
    Check if system is ready for ML training.

    Returns:
        ML readiness status and requirements
    """
    try:
        stats = state.logger.get_statistics()

        requirements = {
            "total_interactions": stats['total_interactions'] >= 20,
            "verified_interactions": stats['verified_interactions'] >= 5,
        }

        all_ready = all(requirements.values())

        return {
            "ready": all_ready,
            "requirements": requirements,
            "current_stats": stats,
            "ml_confidence": min(0.8, (stats['verified_interactions'] / 100) * 0.8)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check ML readiness: {str(e)}")


# ==================== Document Upload Endpoints ====================

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document (PDF, TXT, etc.) for processing.

    Args:
        file: Uploaded file

    Returns:
        Extracted text content
    """
    try:
        # Read file content
        content = await file.read()

        # Initialize processor with API key
        api_key = os.getenv("GEMINI_API_KEY")
        processor = DocumentProcessor(gemini_api_key=api_key)

        # Process document
        processed_doc = processor.process_document(
            file_bytes=content,
            filename=file.filename,
            mime_type=file.content_type
        )

        # Store document in state
        import uuid
        from datetime import datetime
        doc_id = str(uuid.uuid4())
        state.uploaded_documents[doc_id] = {
            "id": doc_id,
            "filename": file.filename,
            "content": processed_doc.content,
            "preview": processed_doc.preview,
            "uploaded_at": datetime.now().isoformat(),
            "metadata": processed_doc.metadata.model_dump()
        }

        return {
            "id": doc_id,
            "filename": file.filename,
            "content": processed_doc.content,
            "preview": processed_doc.preview,
            "metadata": processed_doc.metadata.model_dump()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")


@app.get("/api/documents")
async def list_documents():
    """
    Get list of all uploaded documents.

    Returns:
        List of uploaded documents
    """
    try:
        documents = [
            {
                "id": doc["id"],
                "filename": doc["filename"],
                "preview": doc["preview"],
                "uploaded_at": doc["uploaded_at"]
            }
            for doc in state.uploaded_documents.values()
        ]
        return {"documents": documents}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: str):
    """
    Get a specific document by ID.

    Args:
        doc_id: Document ID

    Returns:
        Document details with full content
    """
    try:
        if doc_id not in state.uploaded_documents:
            raise HTTPException(status_code=404, detail="Document not found")

        return state.uploaded_documents[doc_id]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


# ==================== Note Structuring & Chat Endpoints ====================

@app.post("/api/notes/structure")
async def structure_note(request: StructureNoteRequest):
    """
    Structure a note using AI - converts unstructured text into organized content.

    Args:
        request: Contains note_id and content to structure

    Returns:
        Structured note content with headers, sections, and formatting
    """
    try:
        if not state.api_key:
            raise HTTPException(
                status_code=500,
                detail="Gemini API key not configured. Set GEMINI_API_KEY environment variable."
            )

        generator = AIContentGenerator(api_key=state.api_key)
        structured_content = generator.structure_note(request.content)

        return {
            "note_id": request.note_id,
            "structured_content": structured_content,
            "message": "Note structured successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to structure note: {str(e)}")


@app.post("/api/chat")
async def chat_with_ai(request: ChatRequest):
    """
    Chat with AI about documents, notes, or general questions.

    Args:
        request: Contains message, optional context, source_id, and file_uri

    Returns:
        AI response and optionally updated note content
    """
    try:
        if not state.api_key:
            raise HTTPException(
                status_code=500,
                detail="Gemini API key not configured. Set GEMINI_API_KEY environment variable."
            )

        generator = AIContentGenerator(api_key=state.api_key)
        response = generator.chat(
            message=request.message,
            context=request.context,
            source_id=request.source_id
        )

        return {
            "reply": response["reply"],
            "updated_note_content": response.get("updated_note_content"),
            "message": "Chat response generated"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate chat response: {str(e)}")


# ==================== Health Check ===================="

@app.get("/")
async def root():
    """API health check"""
    return {
        "status": "online",
        "message": "AI Study App API is running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "api_key_configured": state.api_key is not None,
        "flashcards_count": len(state.flashcards),
        "interactions_logged": state.logger.get_statistics()['total_interactions']
    }


# ==================== Run Server ====================

if __name__ == "__main__":
    import uvicorn

    # Load API key from environment
    from dotenv import load_dotenv
    load_dotenv()

    print("Starting AI Study App API...")
    print("API Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/health")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-reload on code changes
    )
