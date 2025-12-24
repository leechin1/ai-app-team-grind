-- ============================================
-- NOTIQ - Complete Supabase Schema V2
-- Project-scoped architecture with RAG support
-- ============================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- ============================================
-- USERS TABLE (extends Supabase auth.users)
-- ============================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- PROJECTS TABLE (Core entity)
-- ============================================
CREATE TABLE IF NOT EXISTS public.projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    icon TEXT DEFAULT '📚',
    color TEXT DEFAULT 'from-blue-500 to-cyan-600',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- NOTES TABLE (Editor content)
-- ============================================
CREATE TABLE IF NOT EXISTS public.notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'Untitled',
    content TEXT DEFAULT '',
    content_html TEXT DEFAULT '',
    course TEXT,
    due_date DATE,
    type TEXT DEFAULT 'Study Notes',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- DOCUMENTS TABLE (Uploaded files)
-- ============================================
CREATE TABLE IF NOT EXISTS public.documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    mime_type TEXT,
    extracted_text TEXT,
    page_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- EMBEDDINGS TABLE (Vector storage for RAG)
-- ============================================
CREATE TABLE IF NOT EXISTS public.embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,

    -- Source reference (note OR document chunk)
    source_type TEXT NOT NULL CHECK (source_type IN ('note', 'document')),
    source_id UUID NOT NULL,

    -- Content
    content TEXT NOT NULL,
    chunk_index INTEGER DEFAULT 0,

    -- Vector embedding (1536 dimensions for OpenAI, 384 for sentence-transformers)
    embedding vector(1536),

    -- Metadata
    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- FLASHCARDS TABLE (SRS study cards)
-- ============================================
CREATE TABLE IF NOT EXISTS public.flashcards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,

    -- Source tracking
    source_type TEXT CHECK (source_type IN ('note', 'document', 'manual')),
    source_id UUID,
    source_name TEXT,

    -- Card content
    front TEXT NOT NULL,
    back TEXT NOT NULL,

    -- SRS fields (SM-2 algorithm)
    easiness_factor FLOAT DEFAULT 2.5,
    interval INTEGER DEFAULT 0,
    repetitions INTEGER DEFAULT 0,
    next_review_date TIMESTAMPTZ DEFAULT NOW(),
    last_review_date TIMESTAMPTZ,

    -- Metadata
    tags TEXT[] DEFAULT '{}',
    difficulty TEXT DEFAULT 'medium' CHECK (difficulty IN ('easy', 'medium', 'hard')),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- FLASHCARD REVIEWS TABLE (Review history)
-- ============================================
CREATE TABLE IF NOT EXISTS public.flashcard_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    flashcard_id UUID NOT NULL REFERENCES public.flashcards(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,

    -- Review data
    quality INTEGER NOT NULL CHECK (quality >= 0 AND quality <= 5),
    time_taken_seconds INTEGER,

    -- SRS state at review time
    easiness_factor FLOAT,
    interval INTEGER,
    repetitions INTEGER,

    reviewed_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- QUIZ QUESTIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS public.quiz_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,

    -- Source tracking
    source_type TEXT CHECK (source_type IN ('note', 'document', 'manual')),
    source_id UUID,
    source_name TEXT,

    -- Question content
    question TEXT NOT NULL,
    options JSONB NOT NULL,
    correct_answer TEXT NOT NULL,
    explanation TEXT,

    -- Metadata
    difficulty TEXT DEFAULT 'medium' CHECK (difficulty IN ('easy', 'medium', 'hard')),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- MATCH PAIRS TABLE (Match quiz)
-- ============================================
CREATE TABLE IF NOT EXISTS public.match_pairs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,

    -- Source tracking
    source_type TEXT CHECK (source_type IN ('note', 'document', 'manual')),
    source_id UUID,
    source_name TEXT,

    -- Pair content
    term TEXT NOT NULL,
    definition TEXT NOT NULL,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- CHAT MESSAGES TABLE (ChatIQ history)
-- ============================================
CREATE TABLE IF NOT EXISTS public.chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,

    -- Message data
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,

    -- Context used (for debugging/analytics)
    context_sources JSONB DEFAULT '[]',

    -- Token usage tracking
    prompt_tokens INTEGER,
    completion_tokens INTEGER,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- INDEXES for Performance
-- ============================================

-- Projects indexes
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON public.projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON public.projects(created_at DESC);

-- Notes indexes
CREATE INDEX IF NOT EXISTS idx_notes_project_id ON public.notes(project_id);
CREATE INDEX IF NOT EXISTS idx_notes_user_id ON public.notes(user_id);
CREATE INDEX IF NOT EXISTS idx_notes_updated_at ON public.notes(updated_at DESC);

-- Documents indexes
CREATE INDEX IF NOT EXISTS idx_documents_project_id ON public.documents(project_id);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON public.documents(user_id);

-- Embeddings indexes
CREATE INDEX IF NOT EXISTS idx_embeddings_project_id ON public.embeddings(project_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_source ON public.embeddings(source_type, source_id);
-- Vector similarity index (IVFFlat for fast approximate search)
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON public.embeddings
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Flashcards indexes
CREATE INDEX IF NOT EXISTS idx_flashcards_project_id ON public.flashcards(project_id);
CREATE INDEX IF NOT EXISTS idx_flashcards_user_id ON public.flashcards(user_id);
CREATE INDEX IF NOT EXISTS idx_flashcards_next_review ON public.flashcards(next_review_date);
CREATE INDEX IF NOT EXISTS idx_flashcards_source ON public.flashcards(source_type, source_id);

-- Flashcard reviews indexes
CREATE INDEX IF NOT EXISTS idx_flashcard_reviews_card_id ON public.flashcard_reviews(flashcard_id);
CREATE INDEX IF NOT EXISTS idx_flashcard_reviews_user_id ON public.flashcard_reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_flashcard_reviews_date ON public.flashcard_reviews(reviewed_at DESC);

-- Quiz indexes
CREATE INDEX IF NOT EXISTS idx_quiz_questions_project_id ON public.quiz_questions(project_id);
CREATE INDEX IF NOT EXISTS idx_match_pairs_project_id ON public.match_pairs(project_id);

-- Chat messages indexes
CREATE INDEX IF NOT EXISTS idx_chat_messages_project_id ON public.chat_messages(project_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON public.chat_messages(created_at DESC);

-- ============================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================

-- Enable RLS on all tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.flashcards ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.flashcard_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.quiz_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.match_pairs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users can view own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

-- Projects policies
CREATE POLICY "Users can view own projects" ON public.projects
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own projects" ON public.projects
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own projects" ON public.projects
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own projects" ON public.projects
    FOR DELETE USING (auth.uid() = user_id);

-- Notes policies
CREATE POLICY "Users can view own notes" ON public.notes
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own notes" ON public.notes
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own notes" ON public.notes
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own notes" ON public.notes
    FOR DELETE USING (auth.uid() = user_id);

-- Documents policies
CREATE POLICY "Users can view own documents" ON public.documents
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own documents" ON public.documents
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own documents" ON public.documents
    FOR DELETE USING (auth.uid() = user_id);

-- Embeddings policies
CREATE POLICY "Users can view own embeddings" ON public.embeddings
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own embeddings" ON public.embeddings
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own embeddings" ON public.embeddings
    FOR DELETE USING (auth.uid() = user_id);

-- Flashcards policies
CREATE POLICY "Users can view own flashcards" ON public.flashcards
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own flashcards" ON public.flashcards
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own flashcards" ON public.flashcards
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own flashcards" ON public.flashcards
    FOR DELETE USING (auth.uid() = user_id);

-- Flashcard reviews policies
CREATE POLICY "Users can view own reviews" ON public.flashcard_reviews
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own reviews" ON public.flashcard_reviews
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Quiz questions policies
CREATE POLICY "Users can view own quiz questions" ON public.quiz_questions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own quiz questions" ON public.quiz_questions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own quiz questions" ON public.quiz_questions
    FOR DELETE USING (auth.uid() = user_id);

-- Match pairs policies
CREATE POLICY "Users can view own match pairs" ON public.match_pairs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own match pairs" ON public.match_pairs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own match pairs" ON public.match_pairs
    FOR DELETE USING (auth.uid() = user_id);

-- Chat messages policies
CREATE POLICY "Users can view own chat messages" ON public.chat_messages
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own chat messages" ON public.chat_messages
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- ============================================
-- FUNCTIONS & TRIGGERS
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON public.projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notes_updated_at BEFORE UPDATE ON public.notes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_flashcards_updated_at BEFORE UPDATE ON public.flashcards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- HELPER FUNCTIONS FOR RAG
-- ============================================

-- Function to search similar embeddings (semantic search)
CREATE OR REPLACE FUNCTION match_embeddings(
    query_embedding vector(1536),
    match_project_id UUID,
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    source_type TEXT,
    source_id UUID,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.id,
        e.content,
        e.source_type,
        e.source_id,
        1 - (e.embedding <=> query_embedding) AS similarity
    FROM public.embeddings e
    WHERE e.project_id = match_project_id
        AND 1 - (e.embedding <=> query_embedding) > match_threshold
    ORDER BY e.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function to get due flashcards for a project
CREATE OR REPLACE FUNCTION get_due_flashcards(
    p_project_id UUID,
    p_user_id UUID,
    p_limit INT DEFAULT 20
)
RETURNS SETOF public.flashcards
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT *
    FROM public.flashcards
    WHERE project_id = p_project_id
        AND user_id = p_user_id
        AND next_review_date <= NOW()
    ORDER BY next_review_date ASC
    LIMIT p_limit;
END;
$$;

-- ============================================
-- INITIAL DATA / DEMO SETUP
-- ============================================

-- This will be handled by the backend when users sign up
-- Demo data can be inserted via the application

-- ============================================
-- VIEWS FOR ANALYTICS (Optional)
-- ============================================

-- View: Project statistics
CREATE OR REPLACE VIEW project_stats AS
SELECT
    p.id AS project_id,
    p.name AS project_name,
    p.user_id,
    COUNT(DISTINCT n.id) AS note_count,
    COUNT(DISTINCT f.id) AS flashcard_count,
    COUNT(DISTINCT d.id) AS document_count,
    COUNT(DISTINCT cm.id) AS chat_message_count,
    MAX(n.updated_at) AS last_note_update
FROM public.projects p
LEFT JOIN public.notes n ON p.id = n.project_id
LEFT JOIN public.flashcards f ON p.id = f.project_id
LEFT JOIN public.documents d ON p.id = d.project_id
LEFT JOIN public.chat_messages cm ON p.id = cm.project_id
GROUP BY p.id, p.name, p.user_id;

-- View: Flashcard review statistics
CREATE OR REPLACE VIEW flashcard_review_stats AS
SELECT
    f.id AS flashcard_id,
    f.user_id,
    f.project_id,
    COUNT(fr.id) AS total_reviews,
    AVG(fr.quality) AS avg_quality,
    MAX(fr.reviewed_at) AS last_reviewed,
    f.easiness_factor,
    f.interval,
    f.next_review_date
FROM public.flashcards f
LEFT JOIN public.flashcard_reviews fr ON f.id = fr.flashcard_id
GROUP BY f.id, f.user_id, f.project_id, f.easiness_factor, f.interval, f.next_review_date;

-- ============================================
-- COMPLETE!
-- ============================================
-- Schema is ready for:
-- ✅ Project-scoped architecture
-- ✅ RAG with vector embeddings
-- ✅ SRS flashcards with review history
-- ✅ Multi-user support with RLS
-- ✅ ChatIQ conversation history
-- ✅ Performance-optimized indexes
-- ============================================
