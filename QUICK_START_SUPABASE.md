# Quick Start: Supabase Integration

## Problem #1: Document Filtering (FIXED ✅)

**Issue**: When reviewing flashcards from Document A, flashcards from Document B were also appearing.

**Solution**: Updated Flashcards page to filter by `documentId` when passed from Review page.

## Problem #2: No Data Persistence

**Issue**: All data is in-memory - lost when server restarts.

**Solution**: Migrate to Supabase PostgreSQL database.

---

## 🚀 5-Minute Setup

### Step 1: Create Supabase Project
1. Go to [supabase.com](https://supabase.com)
2. Create new project (takes 2 mins)
3. Run `supabase_migration.sql` in SQL Editor

### Step 2: Add Environment Variables
Edit `.env`:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
GEMINI_API_KEY=your_existing_key
```

### Step 3: Install Supabase
```bash
cd backend
pip install supabase==2.3.0
```

### Step 4: Implement Backend Changes
Follow `SUPABASE_IMPLEMENTATION.md` for detailed code examples.

---

## 📊 Database Schema Overview

### Core Tables
1. **documents** - Uploaded PDFs/TXT files
2. **flashcards** - SM-2 spaced repetition cards
3. **quizzes** + **quiz_questions** - Multiple choice quizzes
4. **match_quizzes** + **match_pairs** - Matching games
5. **review_logs** - ML training data

### Key Features
- ✅ Foreign keys link content to source documents
- ✅ Indexes for fast filtering and queries
- ✅ Views for common aggregations (stats, due cards)
- ✅ Row Level Security for future multi-user

---

## 📝 What Changed

### Backend
- `AppState` → Supabase database queries
- In-memory dicts → PostgreSQL tables
- JSONL logging → `review_logs` table
- Lost on restart → Persistent storage

### Frontend
- **No changes needed!** Same API contracts

### Models
Added to `FlashCard`, `QuizQuestion`, `MatchPair`:
```python
source_document_id: Optional[str] = None
source_document_name: Optional[str] = None
```

---

## 🎯 Migration Checklist

- [ ] Create Supabase project
- [ ] Run migration SQL
- [ ] Add env variables
- [ ] Install `supabase` package
- [ ] Update document upload endpoint
- [ ] Update flashcard endpoints
- [ ] Update quiz endpoints
- [ ] Update match endpoints
- [ ] Update stats endpoint
- [ ] Test: Upload → Generate → Review
- [ ] Test: Server restart (data persists!)

---

## 📖 Full Documentation

- `SUPABASE_SCHEMA.md` - Complete schema with explanations
- `supabase_migration.sql` - SQL to run in Supabase
- `SUPABASE_IMPLEMENTATION.md` - Step-by-step code guide

---

## 🔥 Benefits

**Before (In-Memory)**:
- ❌ Lost data on restart
- ❌ Limited to single instance
- ❌ No analytics
- ❌ Manual backups

**After (Supabase)**:
- ✅ Persistent data
- ✅ Scalable to millions of records
- ✅ SQL analytics
- ✅ Automatic backups
- ✅ Real-time subscriptions
- ✅ Multi-user ready
- ✅ File storage included

---

## 🧪 Testing After Migration

```bash
# 1. Start backend
cd backend
python main.py

# 2. Start frontend (new terminal)
cd frontend
npm run dev

# 3. Test Flow
1. Upload PDF → Check Supabase "documents" table
2. Generate flashcards → Check "flashcards" table
3. Review flashcards → Check "review_logs" table
4. Stop server → Restart → Data still there! ✅
```

---

## 🆘 Need Help?

Check `SUPABASE_IMPLEMENTATION.md` for:
- Detailed endpoint examples
- Error solutions
- Testing guides
