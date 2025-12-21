# Supabase Implementation Guide

Complete step-by-step guide to migrate Notiq from in-memory storage to Supabase PostgreSQL.

## Phase 1: Supabase Setup (10 minutes)

### 1.1 Create Supabase Project
1. Go to [supabase.com](https://supabase.com) and sign in
2. Click "New Project"
3. Fill in:
   - Project name: `notiq-study-app`
   - Database Password: (save this securely!)
   - Region: Choose closest to you
4. Wait 2-3 minutes for project to spin up

### 1.2 Run Migration SQL
1. In Supabase Dashboard, go to **SQL Editor**
2. Click **New Query**
3. Copy entire contents of `supabase_migration.sql`
4. Paste and click **Run**
5. Verify: Go to **Table Editor** - you should see 7 tables

### 1.3 Get API Credentials
1. Go to **Settings** → **API**
2. Copy and save:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon/public key**: `eyJhbG...` (long string)

## Phase 2: Backend Setup (15 minutes)

### 2.1 Install Supabase Client
```bash
cd backend
pip install supabase==2.3.0
pip freeze > requirements.txt
```

### 2.2 Update Environment Variables
Edit `.env` file in project root:
```bash
GEMINI_API_KEY=your_existing_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

### 2.3 Create Supabase Client Module
Create `backend/core/database.py`:

```python
from supabase import create_client, Client
import os
from typing import Optional

class SupabaseDB:
    _instance: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:
        if cls._instance is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")

            if not url or not key:
                raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")

            cls._instance = create_client(url, key)

        return cls._instance

# Convenience function
def get_db() -> Client:
    return SupabaseDB.get_client()
```

## Phase 3: Update Models (20 minutes)

### 3.1 Add Missing Fields to models.py

Edit `backend/core/models.py` and add to FlashCard class:

```python
class FlashCard(BaseModel):
    # ... existing fields ...

    # ADD THESE FIELDS:
    source_document_id: Optional[str] = None
    source_document_name: Optional[str] = None
```

Do the same for QuizQuestion and MatchPair models.

## Phase 4: Update Backend Endpoints (30-60 minutes)

### 4.1 Document Endpoints

Replace document upload in `main.py`:

```python
from core.database import get_db

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    # ... existing extraction logic ...

    # INSERT into Supabase
    db = get_db()
    result = db.table("documents").insert({
        "filename": file.filename,
        "content": extracted_text,
        "preview": preview_text,
        "file_type": file_ext,
        "file_size": len(file_content),
        "metadata": metadata
    }).execute()

    doc = result.data[0]

    return {
        "id": doc["id"],
        "filename": doc["filename"],
        "content": doc["content"],
        "preview": doc["preview"],
        "metadata": doc["metadata"]
    }

@app.get("/api/documents")
async def list_documents():
    db = get_db()
    result = db.table("documents")\
        .select("id, filename, preview, uploaded_at")\
        .order("uploaded_at", desc=True)\
        .execute()

    return {"documents": result.data}

@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: str):
    db = get_db()
    result = db.table("documents")\
        .select("*")\
        .eq("id", doc_id)\
        .single()\
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Document not found")

    return result.data
```

### 4.2 Flashcard Endpoints

```python
@app.post("/api/flashcards/generate")
async def generate_flashcards(request: FlashcardGenerationRequest):
    # ... existing AI generation logic ...

    # Add source document tracking
    source_doc_id = request.source_document_id  # Add this to request model
    source_doc_name = request.source_document_name

    # INSERT flashcards into Supabase
    db = get_db()
    flashcards_data = [
        {
            "front": card.front,
            "back": card.back,
            "difficulty": card.difficulty,
            "tags": card.tags,
            "source_text": card.source_text,
            "source_document_id": source_doc_id,
            "source_document_name": source_doc_name,
            "interval": 0,
            "repetitions": 0,
            "ease_factor": 2.5,
            "review_count": 0
        }
        for card in generated_flashcards
    ]

    result = db.table("flashcards").insert(flashcards_data).execute()

    return {"flashcards": result.data}

@app.get("/api/flashcards/due")
async def get_due_flashcards():
    db = get_db()
    result = db.table("flashcards")\
        .select("*")\
        .or_("next_review_date.is.null,next_review_date.lte.now()")\
        .order("next_review_date.nullsfirst")\
        .execute()

    return {
        "due_cards": result.data,
        "total_due": len(result.data)
    }

@app.get("/api/flashcards/by-document")
async def get_flashcards_by_document(document_id: Optional[str] = None):
    db = get_db()

    if document_id:
        # Filter by specific document
        result = db.table("flashcards")\
            .select("*")\
            .eq("source_document_id", document_id)\
            .execute()

        return {
            "flashcards": result.data,
            "total": len(result.data),
            "document_id": document_id
        }
    else:
        # Group by document
        result = db.table("flashcards_by_document")\
            .select("*")\
            .execute()

        # Fetch flashcards for each document
        by_document = []
        for doc_group in result.data:
            cards = db.table("flashcards")\
                .select("*")\
                .eq("source_document_id", doc_group["document_id"])\
                .execute()

            by_document.append({
                "document_id": doc_group["document_id"],
                "document_name": doc_group["document_name"],
                "flashcards": cards.data,
                "count": len(cards.data)
            })

        return {
            "by_document": by_document,
            "total": sum(g["count"] for g in by_document)
        }

@app.post("/api/flashcards/review")
async def review_flashcard(request: ReviewFlashcardRequest):
    db = get_db()

    # Get flashcard
    card_result = db.table("flashcards")\
        .select("*")\
        .eq("id", request.flashcard_id)\
        .single()\
        .execute()

    if not card_result.data:
        raise HTTPException(status_code=404, detail="Flashcard not found")

    card_dict = card_result.data
    card = FlashCard(**card_dict)

    # Process with SM-2 algorithm (keep existing logic)
    updated_card = state.sm2.process_review(card, request.response_quality)

    # Update in Supabase
    db.table("flashcards")\
        .update({
            "interval": updated_card.interval,
            "repetitions": updated_card.repetitions,
            "ease_factor": float(updated_card.ease_factor),
            "last_reviewed_at": updated_card.last_reviewed_at.isoformat(),
            "next_review_date": updated_card.next_review_date.isoformat() if updated_card.next_review_date else None,
            "review_count": updated_card.review_count
        })\
        .eq("id", request.flashcard_id)\
        .execute()

    # Log review
    db.table("review_logs").insert({
        "interaction_type": "flashcard_review",
        "flashcard_id": request.flashcard_id,
        "was_correct": request.was_correct,
        "response_quality": request.response_quality,
        "time_spent_seconds": request.time_spent_seconds,
        "confidence_weight": 0.3  # Self-reported
    }).execute()

    return {
        "flashcard": updated_card.model_dump(),
        "stats": state.sm2.get_review_stats(updated_card),
        "message": f"Next review in {updated_card.interval} days"
    }
```

### 4.3 Quiz Endpoints

```python
@app.post("/api/quiz/generate")
async def generate_quiz(request: GenerateQuizRequest):
    # ... existing AI generation logic ...

    db = get_db()

    # Create quiz record
    quiz_result = db.table("quizzes").insert({
        "source_document_id": request.source_document_id,  # Add to request model
        "source_document_name": request.source_document_name,
        "difficulty": request.difficulty,
        "total_questions": len(generated_questions)
    }).execute()

    quiz_id = quiz_result.data[0]["id"]

    # Insert questions
    questions_data = [
        {
            "quiz_id": quiz_id,
            "question": q.question,
            "options": q.options,
            "correct_answer_index": q.correct_answer_index,
            "explanation": q.explanation,
            "concept": q.concept
        }
        for q in generated_questions
    ]

    db.table("quiz_questions").insert(questions_data).execute()

    # Fetch full quiz with questions
    questions_result = db.table("quiz_questions")\
        .select("*")\
        .eq("quiz_id", quiz_id)\
        .execute()

    return {
        "quiz_id": quiz_id,
        "questions": questions_result.data
    }

@app.post("/api/quiz/submit")
async def submit_quiz(request: QuizSubmitRequest):
    db = get_db()

    # Update each question with user's answer
    for answer in request.answers:
        question = db.table("quiz_questions")\
            .select("*")\
            .eq("id", answer.question_id)\
            .single()\
            .execute()

        is_correct = question.data["correct_answer_index"] == answer.user_answer_index

        db.table("quiz_questions")\
            .update({
                "user_answer_index": answer.user_answer_index,
                "is_correct": is_correct,
                "time_spent_seconds": answer.time_spent_seconds
            })\
            .eq("id", answer.question_id)\
            .execute()

    # Calculate score
    questions = db.table("quiz_questions")\
        .select("*")\
        .eq("quiz_id", request.quiz_id)\
        .execute()

    correct_count = sum(1 for q in questions.data if q.get("is_correct"))
    total = len(questions.data)
    score = (correct_count / total) * 100 if total > 0 else 0

    # Update quiz
    db.table("quizzes")\
        .update({
            "completed_at": "now()",
            "score": score
        })\
        .eq("id", request.quiz_id)\
        .execute()

    # Log review
    db.table("review_logs").insert({
        "interaction_type": "quiz_attempt",
        "quiz_id": request.quiz_id,
        "was_correct": score >= 70,
        "accuracy": score,
        "confidence_weight": 0.9  # Verified
    }).execute()

    return {
        "quiz_id": request.quiz_id,
        "score": score,
        "message": "Quiz submitted successfully"
    }
```

### 4.4 Stats Endpoint

```python
@app.get("/api/stats")
async def get_stats():
    db = get_db()

    # Use the study_stats view
    stats_result = db.rpc("study_stats").execute()
    stats = stats_result.data[0] if stats_result.data else {}

    # Get flashcard counts
    flashcard_count = db.table("flashcards").select("id", count="exact").execute()
    due_count = db.table("due_flashcards").select("id", count="exact").execute()

    return {
        "total_interactions": stats.get("total_interactions", 0),
        "verified_interactions": stats.get("verified_interactions", 0),
        "self_reported_interactions": stats.get("total_interactions", 0) - stats.get("verified_interactions", 0),
        "overall_accuracy": stats.get("overall_accuracy", 0),
        "flashcards": {
            "total": flashcard_count.count,
            "due": due_count.count
        },
        "by_type": {
            "flashcard_review": stats.get("flashcard_reviews", 0),
            "quiz_attempt": stats.get("quiz_attempts", 0),
            "match_attempt": stats.get("match_attempts", 0)
        }
    }
```

## Phase 5: Testing (15 minutes)

### 5.1 Test Document Upload
1. Start backend: `python main.py`
2. Go to `http://localhost:5173/upload`
3. Upload a PDF
4. Check Supabase Table Editor → documents table

### 5.2 Test Flashcard Generation
1. Click "Generate Flashcards" from uploaded doc
2. Check flashcards table in Supabase
3. Verify `source_document_id` is populated

### 5.3 Test Review Page
1. Go to `http://localhost:5173/review`
2. Click "Review Flashcards" on a document
3. Verify only flashcards from THAT document appear

### 5.4 Test Persistence
1. Stop backend server
2. Restart it
3. Data should still be there!

## Phase 6: Frontend Updates (Optional)

The frontend API calls remain the same! Supabase is a drop-in replacement on the backend.

## Troubleshooting

### Error: "relation 'documents' does not exist"
- Run the migration SQL again in Supabase SQL Editor

### Error: "SUPABASE_URL not set"
- Check `.env` file exists in project root
- Verify `.env` has both `SUPABASE_URL` and `SUPABASE_KEY`

### Flashcards not filtering by document
- Check `source_document_id` is being passed in generation request
- Verify flashcards table has `source_document_id` column populated

## Next Steps

Once everything works:

1. **Add Supabase Storage** for PDF file storage
2. **Enable Multi-user** by adding authentication
3. **Real-time Updates** using Supabase subscriptions
4. **Analytics Dashboard** using SQL views

## Benefits You'll See

✅ Data persists across restarts
✅ Can handle thousands of flashcards
✅ Easy to query and filter by document
✅ Automatic backups by Supabase
✅ Can scale to multiple users
✅ SQL analytics for insights
