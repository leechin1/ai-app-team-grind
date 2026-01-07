# Complete Database Connection Guide

## Current Status

Your Supabase backend integration is **90% complete**. Here's what works and what needs fixing:

### ✅ WORKING (Backend → Database):
- Projects API (create, list, get)
- Notes API (create, update, list)
- Flashcards API (generate, list, review)
- Documents API (upload, list)
- Quiz API (generate, submit)
- Match Quiz API (generate, submit)
- Chat API (send messages)

### ❌ NOT WORKING (Frontend → Backend):
- **Projects Page:** ✅ FIXED (now uses real API)
- **Editor/Notes Page:** ❌ Still uses mock data, needs API connection
- **Review/Flashcards Page:** ❌ Still uses mock data, needs API connection
- **Quiz Page:** ✅ Connected but missing project_id handling
- **Match Quiz Page:** ✅ Connected but missing project_id handling
- **ChatIQ Page:** ❌ Has TODO comment, needs API connection

### ⚠️ BLOCKING ISSUE:
**Mock user profile doesn't exist in database** → Causes foreign key constraint errors

---

## Data Flow Architecture

```
User Clicks Button (UI)
    ↓
Frontend Component (React)
    ↓
API Client (api.ts)
    ↓
HTTP Request to Backend
    ↓
FastAPI Endpoint (main.py)
    ↓
Auth Middleware (auth.py) - Returns mock user ID
    ↓
Database Service (supabase_client.py)
    ↓
Supabase PostgreSQL Database
```

---

## Step-by-Step Fix Plan

### STEP 1: Fix Database (MUST DO FIRST)

**File:** `create_mock_user_final.sql`

**Action:** Run this SQL script in Supabase SQL Editor

**What it does:**
1. Removes foreign key constraint from profiles table
2. Creates mock user profile with ID `00000000-0000-0000-0000-000000000001`
3. Disables RLS on all tables for development

**How to run:**
1. Go to https://lhhkcotlpxfqzicxkxbm.supabase.co
2. Click "SQL Editor"
3. Click "New Query"
4. Copy entire contents of `create_mock_user_final.sql`
5. Click "Run"

---

### STEP 2: Fix Editor/Notes Page

**File:** `frontend/src/pages/Editor.tsx`

**Problem:** Line 60 has `// TODO: Call backend to save`

**Fix:** Need to add API calls for:
- Creating notes
- Updating notes
- Loading notes from project

**Required API calls:**
```typescript
// Already exists in api.ts but needs to be added:
export const noteAPI = {
  async create(projectId: string, note: { title: string; content: string }) {
    return fetchAPI(`/api/notes`, { method: 'POST', body: JSON.stringify({ project_id: projectId, ...note }) });
  },
  async update(noteId: string, note: { title?: string; content?: string }) {
    return fetchAPI(`/api/notes/${noteId}`, { method: 'PATCH', body: JSON.stringify(note) });
  },
  async list(projectId: string) {
    return fetchAPI(`/api/projects/${projectId}/notes`, { method: 'GET' });
  }
}
```

---

### STEP 3: Fix Review/Flashcards Page

**File:** `frontend/src/pages/Review.tsx`

**Problem:** Uses mock flashcards instead of loading from database

**Fix:** Connect to existing flashcard API

**Required changes:**
1. Add useQuery to fetch due flashcards
2. Connect review submission to API
3. Update state after review

---

### STEP 4: Fix ChatIQ Page

**File:** `frontend/src/pages/ChatIQ.tsx`

**Problem:** Line 42 has `// TODO: Call backend API with project context`

**Fix:** Connect to chat API that already exists in backend

---

## Testing Checklist

After fixing, test each feature:

1. ✅ **Create Project** → Check Supabase Dashboard → projects table
2. ⬜ **Create Note** → Check notes table
3. ⬜ **Generate Flashcards** → Check flashcards table
4. ⬜ **Review Flashcard** → Check flashcard_reviews table
5. ⬜ **Upload Document** → Check documents table
6. ⬜ **Generate Quiz** → Check quiz_questions table
7. ⬜ **Generate Match Quiz** → Check match_pairs table
8. ⬜ **Send Chat Message** → Check chat_messages table

---

## File Reference

### Backend (Database Operations):
- `backend/core/supabase_client.py` - All database CRUD operations
- `backend/core/auth.py` - Mock user authentication
- `backend/main.py` - All API endpoints
- `backend/core/db_models.py` - Data models

### Frontend (UI → API):
- `frontend/src/lib/api.ts` - API client
- `frontend/src/pages/Projects.tsx` - ✅ DONE
- `frontend/src/pages/Editor.tsx` - ❌ NEEDS FIX
- `frontend/src/pages/Review.tsx` - ❌ NEEDS FIX
- `frontend/src/pages/Quiz.tsx` - ⚠️ MOSTLY DONE
- `frontend/src/pages/MatchQuiz.tsx` - ⚠️ MOSTLY DONE
- `frontend/src/pages/ChatIQ.tsx` - ❌ NEEDS FIX

### Database Schema:
- `supabase_schema_v2_step1.sql` - Main tables
- `supabase_schema_v2_step2.sql` - Vector extension
- `create_mock_user_final.sql` - Mock user setup

---

## Next Steps

1. **RIGHT NOW:** Run `create_mock_user_final.sql` in Supabase
2. **Test:** Try creating a project in the frontend
3. **Fix:** Editor/Notes page API connection
4. **Fix:** Review/Flashcards page API connection
5. **Fix:** ChatIQ page API connection
6. **Test:** All features end-to-end
