# AI Study App - API Documentation

## Base URL
```
http://localhost:8000
```

## Interactive Documentation
Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Authentication
Currently no authentication required. In production, add JWT tokens or API keys.

---

## Endpoints

### Health Check

#### `GET /`
Basic health check

**Response:**
```json
{
  "status": "online",
  "message": "AI Study App API is running",
  "version": "1.0.0"
}
```

#### `GET /health`
Detailed health check

**Response:**
```json
{
  "status": "healthy",
  "api_key_configured": true,
  "flashcards_count": 10,
  "interactions_logged": 25
}
```

---

### Flashcard Endpoints

#### `POST /api/flashcards/generate`
Generate flashcards from text content

**Request Body:**
```json
{
  "content": "The mitochondria is the powerhouse of the cell...",
  "num_flashcards": 10,
  "difficulty": "medium",
  "focus_topics": ["biology", "cell"]
}
```

**Response:**
```json
{
  "flashcards": [
    {
      "id": "uuid-here",
      "front": "What is the mitochondria?",
      "back": "The powerhouse of the cell",
      "difficulty": "medium",
      "tags": ["biology", "cell"],
      "interval": 0,
      "repetitions": 0,
      "ease_factor": 2.5,
      "next_review_date": null
    }
  ]
}
```

#### `GET /api/flashcards/due`
Get flashcards due for review

**Response:**
```json
{
  "due_cards": [...],
  "total_due": 5
}
```

#### `GET /api/flashcards/{flashcard_id}`
Get a specific flashcard

**Response:**
```json
{
  "id": "uuid-here",
  "front": "What is DNA?",
  "back": "Deoxyribonucleic acid",
  ...
}
```

#### `POST /api/flashcards/review`
Submit a flashcard review (SM-2 spaced repetition)

**Request Body:**
```json
{
  "flashcard_id": "uuid-here",
  "response_quality": 5,
  "was_correct": true,
  "time_spent_seconds": 3.5
}
```

**Response:**
```json
{
  "flashcard": {...},
  "stats": {
    "total_reviews": 3,
    "consecutive_correct": 2,
    "current_interval_days": 6,
    "ease_factor": 2.6,
    "days_until_review": 6
  },
  "message": "Next review in 6 days"
}
```

---

### Quiz Endpoints

#### `POST /api/quiz/generate`
Generate a multiple-choice quiz

**Request Body:**
```json
{
  "content": "Python is a programming language...",
  "num_questions": 5,
  "difficulty": "medium",
  "focus_topics": ["programming"]
}
```

**Response:**
```json
{
  "quiz_id": "uuid-here",
  "questions": [
    {
      "id": "uuid-here",
      "question": "What is Python?",
      "options": ["A snake", "A programming language", "A tool", "A framework"],
      "correct_answer_index": 1,
      "explanation": "Python is a high-level programming language",
      "concept": "Programming basics"
    }
  ]
}
```

#### `POST /api/quiz/submit`
Submit quiz answers

**Request Body:**
```json
{
  "quiz_id": "uuid-here",
  "answers": [
    {
      "question_id": "uuid-here",
      "user_answer_index": 1,
      "time_spent_seconds": 5.5
    }
  ]
}
```

**Response:**
```json
{
  "quiz_id": "uuid-here",
  "message": "Quiz submitted successfully"
}
```

---

### Match Quiz Endpoints

#### `POST /api/match/generate`
Generate a matching quiz

**Request Body:**
```json
{
  "content": "DNA stores genetic information...",
  "num_pairs": 5,
  "difficulty": "medium",
  "focus_topics": ["biology"]
}
```

**Response:**
```json
{
  "match_quiz_id": "uuid-here",
  "pairs": [
    {
      "id": "uuid-here",
      "prompt": "Powerhouse of the cell",
      "answer": "Mitochondria",
      "hint": "Produces ATP",
      "tags": ["biology", "cell"]
    }
  ]
}
```

#### `POST /api/match/submit`
Submit match quiz answers

**Request Body:**
```json
{
  "match_quiz_id": "uuid-here",
  "answers": [
    {
      "pair_id": "uuid-here",
      "user_matched_index": 0,
      "time_spent_seconds": 2.5
    }
  ]
}
```

**Response:**
```json
{
  "match_quiz_id": "uuid-here",
  "message": "Match quiz submitted successfully"
}
```

---

### Analytics Endpoints

#### `GET /api/stats`
Get overall statistics

**Response:**
```json
{
  "total_interactions": 100,
  "by_type": {
    "flashcard_review": 60,
    "quiz_attempt": 25,
    "match_attempt": 15
  },
  "verified_interactions": 40,
  "self_reported_interactions": 60,
  "overall_accuracy": 85.5,
  "verified_ready_for_ml": true,
  "flashcards": {
    "total": 50,
    "due": 10
  }
}
```

#### `GET /api/stats/ml-readiness`
Check ML training readiness

**Response:**
```json
{
  "ready": false,
  "requirements": {
    "total_interactions": false,
    "verified_interactions": false
  },
  "current_stats": {...},
  "ml_confidence": 0.24
}
```

---

### Document Upload Endpoints

#### `POST /api/documents/upload`
Upload and process a document

**Request:**
- Content-Type: `multipart/form-data`
- Field: `file` (PDF, TXT, etc.)

**Response:**
```json
{
  "filename": "document.pdf",
  "content": "Extracted text content...",
  "preview": "First 500 characters...",
  "metadata": {
    "file_type": "pdf",
    "file_size": 1024,
    "page_count": 10
  }
}
```

---

## Response Quality Scale (SM-2)

When reviewing flashcards, use this 0-5 scale:

| Value | Name | Description |
|-------|------|-------------|
| 0 | COMPLETE_BLACKOUT | Complete memory failure |
| 1 | INCORRECT_EASY_RECALL | Incorrect but felt familiar |
| 2 | INCORRECT_HARD_RECALL | Incorrect after hard thinking |
| 3 | CORRECT_HARD_RECALL | Correct but difficult |
| 4 | CORRECT_HESITATION | Correct with some hesitation |
| 5 | PERFECT_RECALL | Perfect, immediate recall |

---

## Difficulty Levels

| Value | Description |
|-------|-------------|
| "easy" | Easier content |
| "medium" | Medium difficulty (default) |
| "hard" | Advanced content |

---

## Error Responses

All errors return this format:

```json
{
  "detail": "Error message here"
}
```

Common status codes:
- `400` - Bad Request (invalid input)
- `404` - Not Found
- `500` - Internal Server Error

---

## CORS Configuration

The API allows requests from:
- `http://localhost:3000` (React dev server)
- `http://localhost:5173` (Vite dev server)
- `http://127.0.0.1:3000`
- `http://127.0.0.1:5173`

---

## Running the Server

```bash
# Development mode (auto-reload)
python main.py

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## Testing

```bash
# Run API tests
python scripts/test_api.py
```

---

## Environment Variables

Required:
```bash
GEMINI_API_KEY=your-api-key-here
```

Create a `.env` file in the project root:
```
GEMINI_API_KEY=your-key-here
```

---

## Next Steps for Frontend Integration

1. **Install Axios in React:**
   ```bash
   npm install axios
   ```

2. **Create API client:**
   ```javascript
   // src/api/client.js
   import axios from 'axios';

   const api = axios.create({
     baseURL: 'http://localhost:8000',
     headers: {
       'Content-Type': 'application/json'
     }
   });

   export default api;
   ```

3. **Use in components:**
   ```javascript
   import api from './api/client';

   // Generate flashcards
   const response = await api.post('/api/flashcards/generate', {
     content: text,
     num_flashcards: 10,
     difficulty: 'medium'
   });

   // Get due flashcards
   const { data } = await api.get('/api/flashcards/due');

   // Review flashcard
   await api.post('/api/flashcards/review', {
     flashcard_id: id,
     response_quality: 5,
     was_correct: true,
     time_spent_seconds: 3.5
   });
   ```

---

## Production Deployment

For production, consider:
1. **Database**: Replace in-memory storage with PostgreSQL/MongoDB
2. **Authentication**: Add JWT tokens
3. **Rate Limiting**: Prevent API abuse
4. **Caching**: Redis for frequently accessed data
5. **HTTPS**: Use SSL certificates
6. **Environment**: Use production ASGI server (Gunicorn + Uvicorn)
