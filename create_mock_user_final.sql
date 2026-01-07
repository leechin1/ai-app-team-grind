-- ============================================
-- Create Mock User for Development Mode
-- ============================================
-- This script removes foreign key constraints and creates a mock user profile
-- Run this in Supabase SQL Editor to enable development mode

-- Step 1: Drop foreign key constraint from profiles to auth.users
ALTER TABLE public.profiles
DROP CONSTRAINT IF EXISTS profiles_id_fkey;

-- Step 2: Drop foreign key constraint from profiles to auth.users (alternative name)
ALTER TABLE public.profiles
DROP CONSTRAINT IF EXISTS profiles_user_id_fkey;

-- Step 3: Insert or update the mock user profile
INSERT INTO public.profiles (id, email, full_name, created_at, updated_at)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'demo@notiq.app',
    'Demo User',
    NOW(),
    NOW()
)
ON CONFLICT (id)
DO UPDATE SET
    email = EXCLUDED.email,
    full_name = EXCLUDED.full_name,
    updated_at = NOW();

-- Step 4: Also handle if there's a conflict on email
DELETE FROM public.profiles WHERE email = 'demo@notiq.app' AND id != '00000000-0000-0000-0000-000000000001';

-- Step 5: Verify the mock user was created
SELECT
    id,
    email,
    full_name,
    created_at,
    'Mock user created successfully!' as status
FROM public.profiles
WHERE id = '00000000-0000-0000-0000-000000000001';

-- ============================================
-- IMPORTANT: RLS Must Be Disabled
-- ============================================
-- If you get permission errors, make sure RLS is disabled:

ALTER TABLE public.profiles DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.notes DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.flashcards DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.flashcard_reviews DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.quiz_questions DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.match_pairs DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.embeddings DISABLE ROW LEVEL SECURITY;
