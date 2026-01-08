"""
Notiq Backend API v2.0 - Supabase Integration
Complete backend with persistent storage and embeddings
"""

from fastapi import FastAPI, HTTPException, Depends, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Supabase services
from core.supabase_client import db
from core.auth import get_current_user
from core.embeddings_service_supabase import embeddings_service
from core.db_models import (
    ProjectCreate, NoteCreate, NoteUpdate, DocumentCreate,
    FlashcardCreate, FlashcardReviewCreate, EmbeddingCreate,
    ChatMessageCreate
)

# Import AI and other services
from core.ai_generator import AIContentGenerator
from core.models import FlashcardGenerationRequest, DifficultyLevel, FlashCard
from core.spaced_repetition import SM2SpacedRepetition
from core.document_processor import DocumentProcessor

# ==================== FastAPI Setup ====================

app = FastAPI(
    title="Notiq API",
    description="AI study platform with Supabase",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sm2 = SM2SpacedRepetition()

# ==================== Request Models ====================

class ChatRequest(BaseModel):
    project_id: str
    message: str

class ReviewFlashcardRequest(BaseModel):
    flashcard_id: str
    response_quality: int
    time_spent_seconds: Optional[int] = None

# ==================== Health & Test ====================

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "Notiq API v2.0 - Supabase Edition",
        "version": "2.0.0"
    }

@app.get("/health")
async def health_check():
    gemini_ok = os.getenv("GEMINI_API_KEY") is not None
    supabase_ok = os.getenv("SUPABASE_URL") is not None and os.getenv("SUPABASE_ANON_KEY") is not None

    return {
        "status": "healthy" if (gemini_ok and supabase_ok) else "degraded",
        "gemini_configured": gemini_ok,
        "supabase_configured": supabase_ok,
        "database": "supabase",
        "embeddings": "gemini"
    }

@app.get("/api/test-db")
async def test_db():
    """Test database connection"""
    try:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")

        if not url or not key:
            return {"status": "error", "message": "Credentials not configured"}

        client = create_client(url, key)
        result = client.table("profiles").select("*").limit(1).execute()

        return {
            "status": "success",
            "message": "✅ Connected to Supabase!",
            "database": "active"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ==================== Projects ====================

@app.post("/api/projects")
async def create_project(project: ProjectCreate, user: dict = Depends(get_current_user)):
    try:
        return await db.create_project(user["id"], project)
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/projects")
async def get_projects(user: dict = Depends(get_current_user)):
    try:
        projects = await db.get_user_projects(user["id"])
        return {"projects": projects}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/projects/{project_id}")
async def get_project(project_id: str, user: dict = Depends(get_current_user)):
    try:
        project = await db.get_project(project_id, user["id"])
        if not project:
            raise HTTPException(404, "Project not found")
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

# ==================== Notes ====================

@app.post("/api/notes")
async def create_note(note: NoteCreate, user: dict = Depends(get_current_user)):
    try:
        created_note = await db.create_note(user["id"], note)

        # Generate embeddings
        if created_note.content and len(created_note.content) > 50:
            try:
                chunks = embeddings_service.embed_document(created_note.content)
                for chunk in chunks:
                    emb = EmbeddingCreate(
                        project_id=created_note.project_id,
                        source_type="note",
                        source_id=created_note.id,
                        content=chunk["content"],
                        chunk_index=chunk["chunk_index"],
                        embedding=chunk["embedding"],
                        metadata={"title": created_note.title}
                    )
                    await db.create_embedding(user["id"], emb)
                print(f"[OK] Generated {len(chunks)} embeddings")
            except Exception as e:
                print(f"[WARN] Embeddings error: {e}")

        return created_note
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/projects/{project_id}/notes")
async def get_notes(project_id: str, user: dict = Depends(get_current_user)):
    try:
        notes = await db.get_project_notes(project_id, user["id"])
        return {"notes": notes}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/notes/{note_id}")
async def get_note(note_id: str, user: dict = Depends(get_current_user)):
    try:
        note = await db.get_note(note_id, user["id"])
        if not note:
            raise HTTPException(404, "Note not found")
        return note
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

@app.patch("/api/notes/{note_id}")
async def update_note(note_id: str, update: NoteUpdate, user: dict = Depends(get_current_user)):
    try:
        updated = await db.update_note(note_id, user["id"], update)
        if not updated:
            raise HTTPException(404, "Note not found")

        # Regenerate embeddings if content changed
        if update.content and len(update.content) > 50:
            try:
                await db.delete_source_embeddings(note_id, user["id"])
                chunks = embeddings_service.embed_document(update.content)
                for chunk in chunks:
                    emb = EmbeddingCreate(
                        project_id=updated.project_id,
                        source_type="note",
                        source_id=updated.id,
                        content=chunk["content"],
                        chunk_index=chunk["chunk_index"],
                        embedding=chunk["embedding"],
                        metadata={"title": updated.title}
                    )
                    await db.create_embedding(user["id"], emb)
                print(f"[OK] Regenerated {len(chunks)} embeddings")
            except Exception as e:
                print(f"[WARN] Embeddings error: {e}")

        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

# ==================== Documents ====================

@app.post("/api/documents/upload")
async def upload_document(
    project_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """Upload document with persistence to Supabase"""
    try:
        # Read file
        content = await file.read()

        # Process document
        api_key = os.getenv("GEMINI_API_KEY")
        processor = DocumentProcessor(gemini_api_key=api_key)

        processed = processor.process_document(
            file_bytes=content,
            filename=file.filename,
            mime_type=file.content_type
        )

        # Save to database
        doc_data = DocumentCreate(
            project_id=project_id,
            filename=file.filename,
            file_path=f"uploads/{user['id']}/{file.filename}",
            file_size=len(content),
            mime_type=file.content_type,
            extracted_text=processed.content,
            page_count=processed.metadata.num_pages
        )

        document = await db.create_document(user["id"], doc_data)

        # Generate embeddings
        if processed.content and len(processed.content) > 50:
            try:
                chunks = embeddings_service.embed_document(processed.content)
                for chunk in chunks:
                    emb = EmbeddingCreate(
                        project_id=project_id,
                        source_type="document",
                        source_id=document.id,
                        content=chunk["content"],
                        chunk_index=chunk["chunk_index"],
                        embedding=chunk["embedding"],
                        metadata={"filename": file.filename}
                    )
                    await db.create_embedding(user["id"], emb)
                print(f"[OK] Document uploaded + {len(chunks)} embeddings generated")
            except Exception as e:
                print(f"[WARN] Embeddings error: {e}")

        return {
            "id": document.id,
            "filename": file.filename,
            "content": processed.content,
            "preview": processed.preview,
            "metadata": processed.metadata.model_dump()
        }

    except Exception as e:
        print(f"[ERROR] Upload error: {e}")
        raise HTTPException(500, f"Failed to upload: {str(e)}")

@app.get("/api/projects/{project_id}/documents")
async def get_documents(project_id: str, user: dict = Depends(get_current_user)):
    try:
        docs = await db.get_project_documents(project_id, user["id"])
        # Transform documents for frontend compatibility
        transformed_docs = []
        for doc in docs:
            preview = doc.extracted_text[:200] + "..." if doc.extracted_text and len(doc.extracted_text) > 200 else (doc.extracted_text or "")
            transformed_docs.append({
                "id": doc.id,
                "filename": doc.filename,
                "preview": preview,
                "uploaded_at": doc.created_at.isoformat() if hasattr(doc.created_at, 'isoformat') else str(doc.created_at)
            })
        return {"documents": transformed_docs, "total": len(transformed_docs)}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: str, user: dict = Depends(get_current_user)):
    try:
        doc = await db.get_document(doc_id, user["id"])
        if not doc:
            raise HTTPException(404, "Document not found")
        return doc
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

# ==================== Flashcards ====================

@app.post("/api/flashcards/generate")
async def generate_flashcards(
    request: FlashcardGenerationRequest,
    project_id: str,
    user: dict = Depends(get_current_user)
):
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(500, "Gemini API key not configured")

        difficulty = DifficultyLevel(request.difficulty_filter) if request.difficulty_filter else None
        generator = AIContentGenerator(api_key=api_key)

        response = generator.generate_flashcards(
            content=request.content,
            num_cards=request.num_cards,
            difficulty_filter=difficulty
        )

        # Save to database
        for card in response.flashcards:
            card_data = FlashcardCreate(
                project_id=project_id,
                front=card.front,
                back=card.back,
                tags=card.tags,
                difficulty=card.difficulty.value,
                source_type="manual"
            )
            await db.create_flashcard(user["id"], card_data)

        return response
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/projects/{project_id}/flashcards")
async def get_flashcards(project_id: str, user: dict = Depends(get_current_user)):
    try:
        cards = await db.get_project_flashcards(project_id, user["id"])
        return {"flashcards": cards, "total": len(cards)}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/projects/{project_id}/flashcards/due")
async def get_due(project_id: str, limit: int = 20, user: dict = Depends(get_current_user)):
    try:
        due_cards = await db.get_due_flashcards(project_id, user["id"], limit)
        return {"due_cards": due_cards, "total_due": len(due_cards)}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/flashcards/review")
async def review(request: ReviewFlashcardRequest, user: dict = Depends(get_current_user)):
    try:
        card = await db.get_flashcard(request.flashcard_id, user["id"])
        if not card:
            raise HTTPException(404, "Flashcard not found")

        # Convert to FlashCard model for SM-2
        fc = FlashCard(
            id=card.id,
            front=card.front,
            back=card.back,
            difficulty=DifficultyLevel(card.difficulty),
            tags=card.tags,
            interval=card.interval,
            repetitions=card.repetitions,
            ease_factor=card.easiness_factor,
            last_reviewed_at=card.last_review_date,
            next_review_date=card.next_review_date
        )

        # SM-2 processing
        updated = sm2.process_review(fc, request.response_quality)

        # Update database
        update_data = {
            "easiness_factor": updated.ease_factor,
            "interval": updated.interval,
            "repetitions": updated.repetitions,
            "next_review_date": updated.next_review_date.isoformat(),
            "last_review_date": datetime.now().isoformat()
        }
        await db.update_flashcard(request.flashcard_id, user["id"], update_data)

        # Log review
        review_data = FlashcardReviewCreate(
            flashcard_id=request.flashcard_id,
            quality=request.response_quality,
            time_taken_seconds=request.time_spent_seconds
        )
        await db.create_flashcard_review(user["id"], review_data, update_data)

        stats = sm2.get_review_stats(updated)
        return {
            "flashcard": updated.model_dump(),
            "stats": stats,
            "message": f"Next review in {stats['days_until_review']} days"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

# ==================== Chat with RAG ====================

@app.post("/api/chat")
async def chat(request: ChatRequest, user: dict = Depends(get_current_user)):
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(500, "Gemini API not configured")

        # Generate query embedding
        query_emb = embeddings_service.generate_embedding(request.message)

        # Search for context
        context_results = await db.search_embeddings(
            project_id=request.project_id,
            query_embedding=query_emb,
            threshold=0.7,
            limit=5
        )

        # Build context
        context_text = "\n\n".join([
            f"[{r['source_type']}] {r['content']}"
            for r in context_results
        ])

        # Generate response
        generator = AIContentGenerator(api_key=api_key)
        prompt = f"""You are a study assistant. Use this context:

Context:
{context_text}

Question: {request.message}

Answer:"""

        response = generator.chat(message=prompt, context=None, source_id=None)

        # Store messages
        user_msg = ChatMessageCreate(
            project_id=request.project_id,
            role="user",
            content=request.message
        )
        await db.create_chat_message(user["id"], user_msg)

        assistant_msg = ChatMessageCreate(
            project_id=request.project_id,
            role="assistant",
            content=response["reply"],
            context_sources=[
                {"source_type": r["source_type"], "source_id": r["source_id"]}
                for r in context_results
            ]
        )
        await db.create_chat_message(user["id"], assistant_msg)

        return {
            "reply": response["reply"],
            "context_sources": context_results,
            "context_used": len(context_results) > 0
        }
    except Exception as e:
        raise HTTPException(500, str(e))


# ==================== Quiz Endpoints ====================

@app.post("/api/quiz/generate")
async def generate_quiz(
    request: dict,
    user: dict = Depends(get_current_user)
):
    """Generate quiz questions from content using AI"""
    try:
        content = request.get("content", "")
        num_questions = request.get("num_questions", 5)
        difficulty = request.get("difficulty", "medium")
        project_id = request.get("project_id")

        if not project_id:
            raise HTTPException(400, "project_id is required")

        if not content or len(content) < 50:
            raise HTTPException(400, "Content must be at least 50 characters")

        # Generate quiz using AI
        prompt = f"""Generate {num_questions} multiple-choice quiz questions from this content.
Difficulty: {difficulty}

Content:
{content}

Return a JSON array of questions with this exact format:
[
  {{
    "question": "What is...",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Option A",
    "explanation": "Brief explanation..."
  }}
]

Make sure:
- Questions test understanding, not just memorization
- All 4 options are plausible
- Explanations are clear and concise
"""

        response = ai_generator.generate_content(prompt)

        # Parse JSON from response
        import json
        import re

        # Extract JSON from markdown code blocks if present
        json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response["reply"], re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON array directly
            json_match = re.search(r'\[.*\]', response["reply"], re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise HTTPException(500, "Failed to parse AI response")

        questions_data = json.loads(json_str)

        # Save questions to database
        from core.db_models import QuizQuestionCreate
        saved_questions = []

        for q_data in questions_data[:num_questions]:
            question = QuizQuestionCreate(
                project_id=project_id,
                source_type="manual",
                question=q_data["question"],
                options=q_data["options"],
                correct_answer=q_data["correct_answer"],
                explanation=q_data.get("explanation", ""),
                difficulty=difficulty
            )
            saved = await db.create_quiz_question(user["id"], question)
            saved_questions.append(saved)

        # Format response for frontend
        quiz_id = f"quiz_{saved_questions[0].id}"
        formatted_questions = []

        for q in saved_questions:
            # Find correct answer index
            correct_index = q.options.index(q.correct_answer) if q.correct_answer in q.options else 0

            formatted_questions.append({
                "id": q.id,
                "question": q.question,
                "options": q.options,
                "correct_answer_index": correct_index,
                "explanation": q.explanation
            })

        return {
            "quiz_id": quiz_id,
            "questions": formatted_questions
        }

    except json.JSONDecodeError as e:
        raise HTTPException(500, f"Failed to parse AI response: {str(e)}")
    except Exception as e:
        raise HTTPException(500, f"Failed to generate quiz: {str(e)}")


@app.post("/api/quiz/submit")
async def submit_quiz(request: dict, user: dict = Depends(get_current_user)):
    """Submit quiz answers (currently just validates)"""
    try:
        quiz_id = request.get("quiz_id")
        answers = request.get("answers", [])

        # For now, just acknowledge submission
        # Later can add analytics/tracking

        return {
            "quiz_id": quiz_id,
            "message": "Quiz submitted successfully"
        }
    except Exception as e:
        raise HTTPException(500, str(e))


# ==================== Match Quiz Endpoints ====================

@app.post("/api/match/generate")
async def generate_match_quiz(
    request: dict,
    user: dict = Depends(get_current_user)
):
    """Generate match pairs from content or flashcards"""
    try:
        content = request.get("content", "")
        num_pairs = request.get("num_pairs", 5)
        difficulty = request.get("difficulty", "medium")
        project_id = request.get("project_id")
        use_flashcards = not content  # If no content, use flashcards

        if not project_id:
            raise HTTPException(400, "project_id is required")

        pairs_to_save = []

        if use_flashcards:
            # Get flashcards from database
            flashcards = await db.get_project_flashcards(project_id, user["id"])

            if not flashcards:
                raise HTTPException(400, "No flashcards found in this project")

            # Use flashcards as match pairs
            import random
            selected = random.sample(flashcards, min(num_pairs, len(flashcards)))

            from core.db_models import MatchPairCreate
            for fc in selected:
                pair = MatchPairCreate(
                    project_id=project_id,
                    source_type="flashcard",
                    source_id=fc.id,
                    term=fc.front,
                    definition=fc.back
                )
                pairs_to_save.append(pair)

        else:
            # Generate pairs from content using AI
            if len(content) < 50:
                raise HTTPException(400, "Content must be at least 50 characters")

            prompt = f"""Generate {num_pairs} term-definition pairs from this content.
Difficulty: {difficulty}

Content:
{content}

Return a JSON array with this exact format:
[
  {{
    "term": "Key term or concept",
    "definition": "Clear, concise definition"
  }}
]

Make sure:
- Terms are important concepts from the content
- Definitions are accurate and concise
- Pairs are suitable for a matching quiz
"""

            response = ai_generator.generate_content(prompt)

            # Parse JSON from response
            import json
            import re

            json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response["reply"], re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_match = re.search(r'\[.*\]', response["reply"], re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise HTTPException(500, "Failed to parse AI response")

            pairs_data = json.loads(json_str)

            from core.db_models import MatchPairCreate
            for p_data in pairs_data[:num_pairs]:
                pair = MatchPairCreate(
                    project_id=project_id,
                    source_type="manual",
                    term=p_data["term"],
                    definition=p_data["definition"]
                )
                pairs_to_save.append(pair)

        # Save all pairs to database
        saved_pairs = []
        for pair in pairs_to_save:
            saved = await db.create_match_pair(user["id"], pair)
            saved_pairs.append(saved)

        # Format response for frontend
        match_quiz_id = f"match_{saved_pairs[0].id}"
        formatted_pairs = [
            {
                "id": p.id,
                "prompt": p.term,
                "answer": p.definition,
                "tags": []
            }
            for p in saved_pairs
        ]

        return {
            "match_quiz_id": match_quiz_id,
            "pairs": formatted_pairs
        }

    except json.JSONDecodeError as e:
        raise HTTPException(500, f"Failed to parse AI response: {str(e)}")
    except Exception as e:
        raise HTTPException(500, f"Failed to generate match quiz: {str(e)}")


@app.post("/api/match/submit")
async def submit_match_quiz(request: dict, user: dict = Depends(get_current_user)):
    """Submit match quiz answers (currently just validates)"""
    try:
        match_quiz_id = request.get("match_quiz_id")
        answers = request.get("answers", [])

        # For now, just acknowledge submission
        # Later can add analytics/tracking

        return {
            "match_quiz_id": match_quiz_id,
            "message": "Match quiz submitted successfully"
        }
    except Exception as e:
        raise HTTPException(500, str(e))


# ==================== Run ====================

if __name__ == "__main__":
    import uvicorn

    print("=" * 70)
    print("Notiq API v2.0 - Supabase Edition")
    print("=" * 70)
    print("Health: http://localhost:8000/health")
    print("Docs: http://localhost:8000/docs")
    print("Test DB: http://localhost:8000/api/test-db")
    print("=" * 70)

    # Check config
    supabase_url = os.getenv("SUPABASE_URL")
    if supabase_url:
        print(f"[OK] Supabase: {supabase_url[:40]}...")
    else:
        print("[WARN] SUPABASE_URL not set!")

    if os.getenv("SUPABASE_ANON_KEY"):
        print("[OK] Supabase key configured")
    else:
        print("[WARN] SUPABASE_ANON_KEY not set!")

    if os.getenv("GEMINI_API_KEY"):
        print("[OK] Gemini API key configured")
    else:
        print("[WARN] GEMINI_API_KEY not set!")

    print("=" * 70)

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
