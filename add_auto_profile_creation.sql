-- ============================================
-- AUTO-CREATE PROFILE WHEN USER SIGNS UP
-- ============================================
-- This is the standard Supabase pattern
-- When a user registers via Supabase Auth,
-- automatically create their profile

-- Create function to handle new user
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name, created_at, updated_at)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email),
    NOW(),
    NOW()
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger on auth.users
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_user();

-- ============================================
-- FIX FOR YOUR EXISTING USER
-- ============================================
-- Your user exists in auth.users but not in profiles
-- This adds the missing profile

INSERT INTO public.profiles (id, email, full_name, created_at, updated_at)
VALUES (
    '0495dca6-fd8a-471a-9a82-0ed3eb2b3b83',
    'test@notiq.app',
    'Demo User',
    NOW(),
    NOW()
)
ON CONFLICT (id) DO UPDATE SET
    email = EXCLUDED.email,
    updated_at = NOW();

-- Verify
SELECT
    'Profile created!' as status,
    id,
    email,
    full_name,
    created_at
FROM public.profiles
WHERE id = '0495dca6-fd8a-471a-9a82-0ed3eb2b3b83';

-- ============================================
-- EXPLANATION
-- ============================================
-- Going forward, when new users sign up via Supabase Auth:
-- 1. User created in auth.users (by Supabase)
-- 2. Trigger fires automatically
-- 3. Profile created in public.profiles
-- 4. Your app can now create projects for that user!
