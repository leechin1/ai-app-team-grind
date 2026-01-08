# Complete Fix Guide - Profile Creation Issue

## The Problem

**Frontend** uses fake auth with user ID: `"user-demo-123"`
**Backend** hardcodes real user ID: `"0495dca6-fd8a-471a-9a82-0ed3eb2b3b83"`
**Database** has user in `auth.users` but NO profile in `profiles` table

Result: **Foreign key constraint error** when creating projects

---

## Solution: Run ONE SQL Script

This will:
1. ✅ Create your missing profile
2. ✅ Set up auto-profile creation for future users
3. ✅ Make everything work immediately

### Step-by-Step:

1. **Go to Supabase Dashboard**: https://lhhkcotlpxfqzicxkxbm.supabase.co
2. **Click "SQL Editor"** (left sidebar)
3. **Click "New Query"**
4. **Copy and paste this ENTIRE SQL script:**

```sql
-- ============================================
-- AUTO-CREATE PROFILE WHEN USER SIGNS UP
-- ============================================

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
-- FIX YOUR EXISTING USER
-- ============================================

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

-- Verify it worked
SELECT
    'SUCCESS - Profile Created!' as status,
    id,
    email,
    full_name,
    created_at
FROM public.profiles
WHERE id = '0495dca6-fd8a-471a-9a82-0ed3eb2b3b83';
```

5. **Click "Run"**
6. **You should see**: "SUCCESS - Profile Created!" with your user info

---

## Test It Works

After running the SQL:

1. **Go to your app** (http://localhost:5173)
2. **Click "+ New Project"**
3. **Create a project**:
   - Name: "Biology 101"
   - Pick an icon: 🧬
   - Pick a color
   - Click "Create Project"

4. **You should see**: "Project created successfully!" ✅

5. **Verify in Supabase**:
   - Go to Supabase Dashboard → Table Editor
   - Click "projects" table
   - See your new project with `user_id = 0495dca6-fd8a-471a-9a82-0ed3eb2b3b83`

---

## What This SQL Does

### Part 1: Auto-Profile Creation (Future Users)
```sql
CREATE FUNCTION handle_new_user() ...
CREATE TRIGGER on_auth_user_created ...
```
- When someone signs up via Supabase Auth
- Automatically creates their profile in `public.profiles`
- You'll never have this problem again!

### Part 2: Fix Your Existing User
```sql
INSERT INTO public.profiles ...
```
- Creates the missing profile for your current user
- Uses `ON CONFLICT` so it's safe to run multiple times
- Matches the user_id your backend is using

---

## Why This Happens

**Standard Supabase Pattern:**

```
User Signs Up
    ↓
Supabase creates row in auth.users
    ↓
Trigger fires automatically
    ↓
Profile created in public.profiles
    ↓
App can now create projects/notes/etc.
```

**What was missing:** The trigger wasn't set up, so step 3 never happened!

---

## Optional: Update Frontend Auth (NOT REQUIRED)

If you want the frontend to show the correct user info, update this file:

**File:** `frontend/src/lib/auth.ts`

```typescript
const FAKE_USER: User = {
  id: "0495dca6-fd8a-471a-9a82-0ed3eb2b3b83",  // ← Match backend
  email: "test@notiq.app",
  name: "Demo User",
  avatar: "👤"
};
```

But this is **cosmetic only** - the backend already uses the correct ID!

---

## After This Fix

### ✅ Will Work:
- Creating projects
- Creating notes
- Generating flashcards
- Uploading documents
- Everything else!

### 🔄 For Production:
Later, when you want real auth:

1. Keep the `handle_new_user()` trigger
2. Replace frontend fake auth with real Supabase Auth
3. Remove the hardcoded user from `backend/core/auth.py`
4. Use real JWT tokens

---

## Need Help?

If you get errors:
1. Check the SQL output for error messages
2. Make sure you're connected to the right project
3. Try running just the "FIX YOUR EXISTING USER" part first

Once the SQL runs successfully, **everything will work!**
