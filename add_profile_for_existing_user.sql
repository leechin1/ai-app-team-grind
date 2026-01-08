-- Add profile for existing user
-- User ID: 0495dca6-fd8a-471a-9a82-0ed3eb2b3b83
-- Email: test@notiq.app

-- Insert the profile (will skip if already exists)
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
    full_name = EXCLUDED.full_name,
    updated_at = NOW();

-- Verify the profile was created
SELECT id, email, full_name, created_at
FROM public.profiles
WHERE id = '0495dca6-fd8a-471a-9a82-0ed3eb2b3b83';
