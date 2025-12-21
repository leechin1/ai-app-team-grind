# Supabase Database Schema for Notiq Study Platform

This document outlines the complete database schema for migrating from in-memory storage to Supabase PostgreSQL.

## Database Tables

### 1. `documents`
Stores uploaded PDF/TXT files and their extracted content.

```sql
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  filename VARCHAR(255) NOT NULL,
  content TEXT NOT NULL,
  preview TEXT, -- First 500 characters for display
  file_type VARCHAR(10), -- 'pdf', 'txt', etc.
  file_size INTEGER, -- Size in bytes
  uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  metadata JSONB DEFAULT '{}', -- Additional metadata (page count, etc.)
  user_id UUID, -- For future multi-user support
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_uploaded_at ON documents(uploaded_at DESC);
```

### 2. `flashcards`
Stores flashcards with SM-2 spaced repetition data.

```sql
CREATE TABLE flashcards (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  front TEXT NOT NULL CHECK (length(front) >= 1 AND length(front) <= 500),
  back TEXT NOT NULL CHECK (length(back) >= 1 AND length(back) <= 2000),
  difficulty VARCHAR(10) NOT NULL DEFAULT 'medium' CHECK (difficulty IN ('easy', 'medium', 'hard')),
  tags TEXT[] DEFAULT '{}', -- Array of tags
  source_text TEXT, -- Original text excerpt
  source_document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  source_document_name VARCHAR(255), -- Denormalized for performance

  -- SM-2 Spaced Repetition Fields
  interval INTEGER DEFAULT 0 NOT NULL, -- Days until next review
  repetitions INTEGER DEFAULT 0 NOT NULL, -- Consecutive correct reviews
  ease_factor DECIMAL(3,2) DEFAULT 2.5 NOT NULL, -- Difficulty multiplier
  last_reviewed_at TIMESTAMP WITH TIME ZONE,
  next_review_date TIMESTAMP WITH TIME ZONE,
  review_count INTEGER DEFAULT 0 NOT NULL,

  -- Metadata
  user_id UUID, -- For future multi-user support
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_flashcards_source_document ON flashcards(source_document_id);
CREATE INDEX idx_flashcards_next_review ON flashcards(next_review_date) WHERE next_review_date IS NOT NULL;
CREATE INDEX idx_flashcards_user_id ON flashcards(user_id);
CREATE INDEX idx_flashcards_tags ON flashcards USING GIN(tags);
```

### 3. `quizzes`
Stores quiz metadata.

```sql
CREATE TABLE quizzes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  source_document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  source_document_name VARCHAR(255),
  difficulty VARCHAR(10) DEFAULT 'medium' CHECK (difficulty IN ('easy', 'medium', 'hard')),
  total_questions INTEGER NOT NULL,
  user_id UUID,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE,
  score DECIMAL(5,2), -- Percentage score (0-100)
  time_spent_seconds INTEGER
);

CREATE INDEX idx_quizzes_source_document ON quizzes(source_document_id);
CREATE INDEX idx_quizzes_user_id ON quizzes(user_id);
CREATE INDEX idx_quizzes_created_at ON quizzes(created_at DESC);
```

### 4. `quiz_questions`
Stores individual quiz questions.

```sql
CREATE TABLE quiz_questions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  quiz_id UUID NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
  question TEXT NOT NULL,
  options TEXT[] NOT NULL, -- Array of 4 options
  correct_answer_index INTEGER NOT NULL CHECK (correct_answer_index >= 0 AND correct_answer_index <= 3),
  explanation TEXT,
  concept VARCHAR(255), -- Main concept being tested
  user_answer_index INTEGER, -- User's selected answer
  is_correct BOOLEAN,
  time_spent_seconds DECIMAL(10,2),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_quiz_questions_quiz_id ON quiz_questions(quiz_id);
```

### 5. `match_quizzes`
Stores match quiz metadata.

```sql
CREATE TABLE match_quizzes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  source_document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  source_document_name VARCHAR(255),
  difficulty VARCHAR(10) DEFAULT 'medium' CHECK (difficulty IN ('easy', 'medium', 'hard')),
  total_pairs INTEGER NOT NULL,
  user_id UUID,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE,
  score DECIMAL(5,2), -- Percentage score (0-100)
  time_spent_seconds INTEGER
);

CREATE INDEX idx_match_quizzes_source_document ON match_quizzes(source_document_id);
CREATE INDEX idx_match_quizzes_user_id ON match_quizzes(user_id);
CREATE INDEX idx_match_quizzes_created_at ON match_quizzes(created_at DESC);
```

### 6. `match_pairs`
Stores match quiz pairs (prompt/answer).

```sql
CREATE TABLE match_pairs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  match_quiz_id UUID NOT NULL REFERENCES match_quizzes(id) ON DELETE CASCADE,
  prompt TEXT NOT NULL,
  answer TEXT NOT NULL,
  hint TEXT,
  tags TEXT[] DEFAULT '{}',
  user_matched_answer TEXT, -- User's matched answer
  is_correct BOOLEAN,
  time_spent_seconds DECIMAL(10,2),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_match_pairs_match_quiz_id ON match_pairs(match_quiz_id);
```

### 7. `review_logs`
Stores all user interactions for ML training data.

```sql
CREATE TABLE review_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  interaction_type VARCHAR(20) NOT NULL CHECK (interaction_type IN ('flashcard_review', 'quiz_attempt', 'match_attempt')),

  -- Reference to the item being reviewed
  flashcard_id UUID REFERENCES flashcards(id) ON DELETE SET NULL,
  quiz_id UUID REFERENCES quizzes(id) ON DELETE SET NULL,
  match_quiz_id UUID REFERENCES match_quizzes(id) ON DELETE SET NULL,

  -- Performance data
  was_correct BOOLEAN,
  response_quality INTEGER CHECK (response_quality >= 0 AND response_quality <= 5), -- For flashcards (SM-2)
  time_spent_seconds DECIMAL(10,2),
  accuracy DECIMAL(5,2), -- For quizzes/matches (0-100)

  -- ML confidence weighting
  confidence_weight DECIMAL(3,2) DEFAULT 0.3, -- 0.3 for self-reported, 0.9 for verified

  -- Metadata
  user_id UUID,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  metadata JSONB DEFAULT '{}' -- Additional context
);

CREATE INDEX idx_review_logs_interaction_type ON review_logs(interaction_type);
CREATE INDEX idx_review_logs_flashcard_id ON review_logs(flashcard_id);
CREATE INDEX idx_review_logs_quiz_id ON review_logs(quiz_id);
CREATE INDEX idx_review_logs_match_quiz_id ON review_logs(match_quiz_id);
CREATE INDEX idx_review_logs_created_at ON review_logs(created_at DESC);
CREATE INDEX idx_review_logs_user_id ON review_logs(user_id);
```

### 8. `users` (Optional - for future multi-user support)
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email VARCHAR(255) UNIQUE,
  full_name VARCHAR(255),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_login_at TIMESTAMP WITH TIME ZONE,
  preferences JSONB DEFAULT '{}'
);

CREATE INDEX idx_users_email ON users(email);
```

## Row Level Security (RLS) Policies

Enable RLS for multi-user support in the future:

```sql
-- Enable RLS on all tables
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE flashcards ENABLE ROW LEVEL SECURITY;
ALTER TABLE quizzes ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE match_quizzes ENABLE ROW LEVEL SECURITY;
ALTER TABLE match_pairs ENABLE ROW LEVEL SECURITY;
ALTER TABLE review_logs ENABLE ROW LEVEL SECURITY;

-- For now, allow all operations (single-user mode)
-- Later, add user_id filtering policies
CREATE POLICY "Allow all for now" ON documents FOR ALL USING (true);
CREATE POLICY "Allow all for now" ON flashcards FOR ALL USING (true);
CREATE POLICY "Allow all for now" ON quizzes FOR ALL USING (true);
CREATE POLICY "Allow all for now" ON quiz_questions FOR ALL USING (true);
CREATE POLICY "Allow all for now" ON match_quizzes FOR ALL USING (true);
CREATE POLICY "Allow all for now" ON match_pairs FOR ALL USING (true);
CREATE POLICY "Allow all for now" ON review_logs FOR ALL USING (true);
```

## Useful Views

### View: Due Flashcards
```sql
CREATE OR REPLACE VIEW due_flashcards AS
SELECT *
FROM flashcards
WHERE next_review_date IS NULL
   OR next_review_date <= NOW()
ORDER BY next_review_date NULLS FIRST, created_at DESC;
```

### View: Study Statistics
```sql
CREATE OR REPLACE VIEW study_stats AS
SELECT
  COUNT(*) FILTER (WHERE interaction_type = 'flashcard_review') as flashcard_reviews,
  COUNT(*) FILTER (WHERE interaction_type = 'quiz_attempt') as quiz_attempts,
  COUNT(*) FILTER (WHERE interaction_type = 'match_attempt') as match_attempts,
  COUNT(*) FILTER (WHERE confidence_weight >= 0.8) as verified_interactions,
  COUNT(*) as total_interactions,
  AVG(accuracy) FILTER (WHERE accuracy IS NOT NULL) as overall_accuracy
FROM review_logs;
```

## Migration Steps

### Step 1: Set up Supabase Project
1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Save your project URL and API keys

### Step 2: Run Migration
1. Copy the SQL above into Supabase SQL Editor
2. Run each section in order:
   - Tables
   - Indexes
   - RLS Policies
   - Views

### Step 3: Install Supabase Client
```bash
cd backend
pip install supabase
```

Update `backend/requirements.txt`:
```
supabase==2.3.0
```

### Step 4: Environment Variables
Add to your `.env` file:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
GEMINI_API_KEY=your_existing_key
```

### Step 5: Update Backend Code
- Replace in-memory `AppState` with Supabase queries
- Update all endpoints to use Supabase CRUD operations
- Keep SM-2 algorithm logic in Python (call it before DB updates)

## Benefits of Supabase Migration

✅ **Persistence** - Data survives server restarts
✅ **Scalability** - PostgreSQL can handle millions of records
✅ **Real-time** - Supabase provides real-time subscriptions
✅ **Backup** - Automatic daily backups
✅ **Multi-user Ready** - RLS policies for user isolation
✅ **Analytics** - SQL queries for powerful insights
✅ **File Storage** - Can store PDFs in Supabase Storage
