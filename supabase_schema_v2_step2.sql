-- ============================================
-- NOTIQ - Supabase Schema V2 - STEP 2
-- Run this AFTER enabling pgvector extension
-- Adds embeddings table and RAG functions
-- ============================================

-- Verify pgvector is enabled
-- If this fails, go to Database > Extensions and enable "vector"
CREATE EXTENSION IF NOT EXISTS "pgvector";

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
-- EMBEDDINGS INDEXES
-- ============================================

CREATE INDEX IF NOT EXISTS idx_embeddings_project_id ON public.embeddings(project_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_source ON public.embeddings(source_type, source_id);

-- Vector similarity index (IVFFlat for fast approximate search)
-- Note: This index is most effective with >1000 vectors
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON public.embeddings
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================
-- EMBEDDINGS RLS POLICIES
-- ============================================

ALTER TABLE public.embeddings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own embeddings" ON public.embeddings
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own embeddings" ON public.embeddings
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own embeddings" ON public.embeddings
    FOR DELETE USING (auth.uid() = user_id);

-- ============================================
-- RAG HELPER FUNCTIONS
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

-- ============================================
-- STEP 2 COMPLETE!
-- ============================================
-- You now have full RAG support with:
-- ✅ Embeddings table with vector storage
-- ✅ IVFFlat index for fast similarity search
-- ✅ match_embeddings() function for semantic search
-- ✅ RLS policies for security
-- ============================================
