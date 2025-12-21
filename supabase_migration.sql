-- Notiq Study Platform - Supabase Migration
-- Run this SQL in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==================== TABLES ====================

-- 1. Documents Table
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  filename VARCHAR(255) NOT NULL,
  content TEXT NOT NULL,
  preview TEXT,
  file_type VARCHAR(10),
  file_size INTEGER,
  uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  metadata JSONB DEFAULT '{}',
  user_id UUID,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Flashcards Table
CREATE TABLE flashcards (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  front TEXT NOT NULL CHECK (length(front) >= 1 AND length(front) <= 500),
  back TEXT NOT NULL CHECK (length(back) >= 1 AND length(back) <= 2000),
  difficulty VARCHAR(10) NOT NULL DEFAULT 'medium' CHECK (difficulty IN ('easy', 'medium', 'hard')),
  tags TEXT[] DEFAULT '{}',
  source_text TEXT,
  source_document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  source_document_name VARCHAR(255),

  -- SM-2 Fields
  interval INTEGER DEFAULT 0 NOT NULL,
  repetitions INTEGER DEFAULT 0 NOT NULL,
  ease_factor DECIMAL(3,2) DEFAULT 2.5 NOT NULL,
  last_reviewed_at TIMESTAMP WITH TIME ZONE,
  next_review_date TIMESTAMP WITH TIME ZONE,
  review_count INTEGER DEFAULT 0 NOT NULL,

  -- Metadata
  user_id UUID,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Quizzes Table
CREATE TABLE quizzes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  source_document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  source_document_name VARCHAR(255),
  difficulty VARCHAR(10) DEFAULT 'medium' CHECK (difficulty IN ('easy', 'medium', 'hard')),
  total_questions INTEGER NOT NULL,
  user_id UUID,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE,
  score DECIMAL(5,2),
  time_spent_seconds INTEGER
);

-- 4. Quiz Questions Table
CREATE TABLE quiz_questions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  quiz_id UUID NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
  question TEXT NOT NULL,
  options TEXT[] NOT NULL,
  correct_answer_index INTEGER NOT NULL CHECK (correct_answer_index >= 0 AND correct_answer_index <= 3),
  explanation TEXT,
  concept VARCHAR(255),
  user_answer_index INTEGER,
  is_correct BOOLEAN,
  time_spent_seconds DECIMAL(10,2),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Match Quizzes Table
CREATE TABLE match_quizzes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  source_document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  source_document_name VARCHAR(255),
  difficulty VARCHAR(10) DEFAULT 'medium' CHECK (difficulty IN ('easy', 'medium', 'hard')),
  total_pairs INTEGER NOT NULL,
  user_id UUID,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE,
  score DECIMAL(5,2),
  time_spent_seconds INTEGER
);

-- 6. Match Pairs Table
CREATE TABLE match_pairs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  match_quiz_id UUID NOT NULL REFERENCES match_quizzes(id) ON DELETE CASCADE,
  prompt TEXT NOT NULL,
  answer TEXT NOT NULL,
  hint TEXT,
  tags TEXT[] DEFAULT '{}',
  user_matched_answer TEXT,
  is_correct BOOLEAN,
  time_spent_seconds DECIMAL(10,2),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. Review Logs Table (ML Training Data)
CREATE TABLE review_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  interaction_type VARCHAR(20) NOT NULL CHECK (interaction_type IN ('flashcard_review', 'quiz_attempt', 'match_attempt')),
  flashcard_id UUID REFERENCES flashcards(id) ON DELETE SET NULL,
  quiz_id UUID REFERENCES quizzes(id) ON DELETE SET NULL,
  match_quiz_id UUID REFERENCES match_quizzes(id) ON DELETE SET NULL,
  was_correct BOOLEAN,
  response_quality INTEGER CHECK (response_quality >= 0 AND response_quality <= 5),
  time_spent_seconds DECIMAL(10,2),
  accuracy DECIMAL(5,2),
  confidence_weight DECIMAL(3,2) DEFAULT 0.3,
  user_id UUID,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  metadata JSONB DEFAULT '{}'
);

-- ==================== INDEXES ====================

-- Documents
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_uploaded_at ON documents(uploaded_at DESC);

-- Flashcards
CREATE INDEX idx_flashcards_source_document ON flashcards(source_document_id);
CREATE INDEX idx_flashcards_next_review ON flashcards(next_review_date) WHERE next_review_date IS NOT NULL;
CREATE INDEX idx_flashcards_user_id ON flashcards(user_id);
CREATE INDEX idx_flashcards_tags ON flashcards USING GIN(tags);

-- Quizzes
CREATE INDEX idx_quizzes_source_document ON quizzes(source_document_id);
CREATE INDEX idx_quizzes_user_id ON quizzes(user_id);
CREATE INDEX idx_quizzes_created_at ON quizzes(created_at DESC);

-- Quiz Questions
CREATE INDEX idx_quiz_questions_quiz_id ON quiz_questions(quiz_id);

-- Match Quizzes
CREATE INDEX idx_match_quizzes_source_document ON match_quizzes(source_document_id);
CREATE INDEX idx_match_quizzes_user_id ON match_quizzes(user_id);
CREATE INDEX idx_match_quizzes_created_at ON match_quizzes(created_at DESC);

-- Match Pairs
CREATE INDEX idx_match_pairs_match_quiz_id ON match_pairs(match_quiz_id);

-- Review Logs
CREATE INDEX idx_review_logs_interaction_type ON review_logs(interaction_type);
CREATE INDEX idx_review_logs_flashcard_id ON review_logs(flashcard_id);
CREATE INDEX idx_review_logs_quiz_id ON review_logs(quiz_id);
CREATE INDEX idx_review_logs_match_quiz_id ON review_logs(match_quiz_id);
CREATE INDEX idx_review_logs_created_at ON review_logs(created_at DESC);
CREATE INDEX idx_review_logs_user_id ON review_logs(user_id);

-- ==================== ROW LEVEL SECURITY ====================

ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE flashcards ENABLE ROW LEVEL SECURITY;
ALTER TABLE quizzes ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE match_quizzes ENABLE ROW LEVEL SECURITY;
ALTER TABLE match_pairs ENABLE ROW LEVEL SECURITY;
ALTER TABLE review_logs ENABLE ROW LEVEL SECURITY;

-- Allow all for now (single-user mode)
CREATE POLICY "Allow all for now" ON documents FOR ALL USING (true);
CREATE POLICY "Allow all for now" ON flashcards FOR ALL USING (true);
CREATE POLICY "Allow all for now" ON quizzes FOR ALL USING (true);
CREATE POLICY "Allow all for now" ON quiz_questions FOR ALL USING (true);
CREATE POLICY "Allow all for now" ON match_quizzes FOR ALL USING (true);
CREATE POLICY "Allow all for now" ON match_pairs FOR ALL USING (true);
CREATE POLICY "Allow all for now" ON review_logs FOR ALL USING (true);

-- ==================== VIEWS ====================

-- Due Flashcards View
CREATE OR REPLACE VIEW due_flashcards AS
SELECT *
FROM flashcards
WHERE next_review_date IS NULL
   OR next_review_date <= NOW()
ORDER BY next_review_date NULLS FIRST, created_at DESC;

-- Study Statistics View
CREATE OR REPLACE VIEW study_stats AS
SELECT
  COUNT(*) FILTER (WHERE interaction_type = 'flashcard_review') as flashcard_reviews,
  COUNT(*) FILTER (WHERE interaction_type = 'quiz_attempt') as quiz_attempts,
  COUNT(*) FILTER (WHERE interaction_type = 'match_attempt') as match_attempts,
  COUNT(*) FILTER (WHERE confidence_weight >= 0.8) as verified_interactions,
  COUNT(*) as total_interactions,
  COALESCE(AVG(accuracy) FILTER (WHERE accuracy IS NOT NULL), 0) as overall_accuracy
FROM review_logs;

-- Flashcards by Document View
CREATE OR REPLACE VIEW flashcards_by_document AS
SELECT
  COALESCE(source_document_id::text, 'manual') as document_id,
  COALESCE(source_document_name, 'Manual Entry') as document_name,
  COUNT(*) as flashcard_count,
  AVG(ease_factor) as avg_ease_factor,
  COUNT(*) FILTER (WHERE next_review_date IS NOT NULL AND next_review_date <= NOW()) as due_count
FROM flashcards
GROUP BY source_document_id, source_document_name;

-- ==================== FUNCTIONS ====================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_flashcards_updated_at BEFORE UPDATE ON flashcards
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
