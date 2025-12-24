# 🚀 Supabase Setup Guide - Notiq V2

This guide will walk you through setting up Supabase for the Notiq application with complete project-scoped architecture and RAG support.

## 📋 Prerequisites

- Supabase account ([Sign up here](https://supabase.com))
- Project ready to connect

## 🎯 Step 1: Create New Supabase Project

1. Go to [https://supabase.com/dashboard](https://supabase.com/dashboard)
2. Click **"New Project"**
3. Fill in:
   - **Name:** `notiq-production` (or your preferred name)
   - **Database Password:** (save this securely!)
   - **Region:** Choose closest to your users
4. Click **"Create new project"**
5. Wait ~2 minutes for provisioning

## 🗄️ Step 2: Run Database Schema

1. In Supabase Dashboard, go to **SQL Editor** (left sidebar)
2. Click **"New Query"**
3. Copy the entire contents of `supabase_schema_v2.sql`
4. Paste into the SQL editor
5. Click **"Run"** (or press Ctrl/Cmd + Enter)

You should see:
```
Success. No rows returned
```

This creates:
- ✅ 10 tables (profiles, projects, notes, documents, embeddings, flashcards, etc.)
- ✅ All indexes for performance
- ✅ RLS policies for security
- ✅ Helper functions for RAG
- ✅ pgvector extension for embeddings

## 🔑 Step 3: Get API Credentials

1. Go to **Settings** → **API** (left sidebar)
2. Copy these values:

```bash
# Project URL
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co

# anon/public key (safe to use in frontend)
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# service_role key (NEVER expose in frontend - backend only!)
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## ⚙️ Step 4: Configure Environment Variables

Update your `.env` file in the backend directory:

```bash
# Supabase Configuration
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_role_key_here

# Existing keys (keep these)
GOOGLE_API_KEY=your_gemini_key
LANGFUSE_PUBLIC_KEY=your_langfuse_key
LANGFUSE_SECRET_KEY=your_langfuse_secret
LANGFUSE_HOST=https://cloud.langfuse.com
```

## 🔐 Step 5: Enable Email Auth (Optional but Recommended)

For production, replace fake auth with real authentication:

1. Go to **Authentication** → **Providers**
2. Enable **Email** provider
3. Configure:
   - ✅ Enable email confirmations
   - ✅ Set up email templates
   - (Optional) Enable OAuth providers (Google, GitHub, etc.)

## 📊 Step 6: Verify Setup

Run these queries in SQL Editor to verify:

```sql
-- Check tables were created
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- Check pgvector extension
SELECT * FROM pg_extension WHERE extname = 'pgvector';

-- Check RLS is enabled
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public';
```

Expected results:
- 10 tables listed
- pgvector extension present
- All tables have `rowsecurity = true`

## 🧪 Step 7: Test Connection

Create a test user and project:

```sql
-- Insert test profile (replace with actual auth user ID later)
INSERT INTO public.profiles (id, email, full_name)
VALUES
  ('00000000-0000-0000-0000-000000000001', 'test@notiq.app', 'Test User')
ON CONFLICT (id) DO NOTHING;

-- Insert test project
INSERT INTO public.projects (user_id, name, description, icon)
VALUES
  ('00000000-0000-0000-0000-000000000001', 'Optimization Algorithms', 'Study notes for CS301', '🎯')
RETURNING *;
```

## 📦 Next Steps

Now that Supabase is set up, you need to:

1. **Update Backend Models** - Modify Pydantic models to match new schema
2. **Replace In-Memory Storage** - Update all API endpoints to use Supabase
3. **Implement Auth** - Connect Supabase auth with the backend
4. **Add Embeddings** - Implement vector generation for RAG
5. **Test Everything** - Verify all features work with database

## 🔍 Database Schema Overview

### Core Tables

| Table | Purpose | Key Features |
|-------|---------|--------------|
| `profiles` | User info | Extends auth.users |
| `projects` | Project containers | User-owned, scoped context |
| `notes` | Editor content | Quill HTML + metadata |
| `documents` | Uploaded files | Text extraction, chunks |
| `embeddings` | Vector storage | 1536-dim OpenAI embeddings |
| `flashcards` | SRS study cards | SM-2 algorithm fields |
| `flashcard_reviews` | Review history | Analytics & ML training data |
| `quiz_questions` | Quiz content | Multiple choice |
| `match_pairs` | Match quiz | Term-definition pairs |
| `chat_messages` | ChatIQ history | Conversation + context tracking |

### Key Features

**🔒 Security:**
- Row Level Security (RLS) on all tables
- Users can only access their own data
- Service role key for backend operations

**⚡ Performance:**
- Indexes on all foreign keys
- Vector similarity index (IVFFlat)
- Optimized for project-scoped queries

**🤖 RAG Support:**
- pgvector for semantic search
- `match_embeddings()` function for similarity search
- Supports both note and document embeddings

**📈 Analytics:**
- Review history tracking
- Token usage tracking
- Project statistics views

## 🆘 Troubleshooting

### "permission denied for table X"
- **Cause:** RLS is blocking access
- **Fix:** Make sure queries use the authenticated user's ID
- **Check:** Verify RLS policies in SQL Editor

### "function vector_cosine_ops does not exist"
- **Cause:** pgvector extension not loaded
- **Fix:** Run `CREATE EXTENSION IF NOT EXISTS "pgvector";`

### "duplicate key value violates unique constraint"
- **Cause:** Trying to insert duplicate data
- **Fix:** Use `ON CONFLICT` clauses or check for existing records first

### Slow vector similarity searches
- **Cause:** Index not created or table too small
- **Fix:** Run the IVFFlat index creation (in schema)
- **Note:** Need at least 1000 vectors for index to be effective

## 📚 Resources

- [Supabase Documentation](https://supabase.com/docs)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [Row Level Security Guide](https://supabase.com/docs/guides/auth/row-level-security)
- [Vector Embeddings Guide](https://supabase.com/docs/guides/ai/vector-embeddings)

## ✅ Checklist

Before moving to backend integration:

- [ ] Supabase project created
- [ ] Schema SQL executed successfully
- [ ] All 10 tables visible in Table Editor
- [ ] pgvector extension enabled
- [ ] API credentials copied to `.env`
- [ ] Test queries run successfully
- [ ] RLS policies verified

Ready to proceed? Next step: **Update Backend Models & API Endpoints**
