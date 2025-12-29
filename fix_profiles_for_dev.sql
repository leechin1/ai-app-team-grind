-- Fix profiles table for development mode
-- This removes the foreign key constraint to auth.users so we can create mock profiles

-- 1. Drop the foreign key constraint
ALTER TABLE public.profiles
DROP CONSTRAINT IF EXISTS profiles_id_fkey;

-- 2. Make id column nullable initially (just in case)
ALTER TABLE public.profiles
ALTER COLUMN id DROP NOT NULL;

ALTER TABLE public.profiles
ALTER COLUMN id SET NOT NULL;

-- 3. Insert mock user profile for development
INSERT INTO public.profiles (id, email, full_name, created_at, updated_at)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'demo@notiq.app',
    'Demo User',
    NOW(),
    NOW()
)
ON CONFLICT (id) DO UPDATE SET
    email = EXCLUDED.email,
    full_name = EXCLUDED.full_name,
    updated_at = NOW();

-- Verify
SELECT id, email, full_name, created_at
FROM public.profiles
WHERE id = '00000000-0000-0000-0000-000000000001';
