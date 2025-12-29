# 🧪 Quick Test Guide - Verify Supabase Integration

Follow these steps to test your Supabase integration:

---

## Step 1: Disable RLS (Required First!)

1. **Open Supabase Dashboard**
   - Go to: https://lhhkcotlpxfqzicxkxbm.supabase.co
   - Click **SQL Editor**

2. **Run the RLS Disable Script**
   - Copy all contents from `disable_rls_for_dev.sql`
   - Paste into SQL Editor
   - Click **"Run"**
   - Should see: "Success. No rows returned"

3. **Verify RLS is Disabled**
   ```sql
   SELECT schemaname, tablename, rowsecurity
   FROM pg_tables
   WHERE schemaname = 'public' AND rowsecurity = true;
   ```
   - Should return **0 rows** (empty result)

---

## Step 2: Run Test Script to Populate Database

This will create a test project with notes and flashcards:

```bash
# Navigate to your project directory
cd "c:\Users\Cícero Santos\Documents\GitHub\ai-app-team-grind"

# Run the test script
python test_database.py
```

**Expected Output:**
```
✅ Database connected successfully!
✅ Project created: 🧪 Test Project - Biology 101
✅ Note created: Cell Structure
✅ Note created: DNA and RNA
✅ Note created: Photosynthesis
✅ Flashcard created (DUE FOR REVIEW): What is the powerhouse of the cell?
✅ Flashcard created (DUE FOR REVIEW): What is the difference between DNA and RNA?
✅ Flashcard created (DUE FOR REVIEW): What is the formula for photosynthesis?
✅ Flashcard created (future review): What are the stages of mitosis?
✅ Flashcard created (future review): What is the function of ribosomes?

📊 SUMMARY
Project ID: <some-uuid>
Total Notes: 3
Total Flashcards: 5
Due for Review: 3
```

---

## Step 3: Verify in Supabase Dashboard

1. **Go to Supabase Dashboard → Table Editor**
2. **Check each table:**

   - **projects** → Should see "🧪 Test Project - Biology 101"
   - **notes** → Should see 3 notes
   - **flashcards** → Should see 5 flashcards
   - **embeddings** → Should be empty (no embeddings generated yet)

---

## Step 4: Test Frontend

1. **Start your frontend** (if not already running)
   ```bash
   cd frontend
   npm run dev
   ```

2. **Open browser**: http://localhost:5173

3. **Check Dashboard:**
   - Should see the test project "🧪 Test Project - Biology 101"
   - Click on it to open

4. **Check Notes:**
   - Navigate to Notes section
   - Should see 3 notes:
     - Cell Structure
     - DNA and RNA
     - Photosynthesis

5. **Check Flashcard Review:**
   - Navigate to Review/Flashcards section
   - Should see 3 cards due for review
   - Try reviewing one card
   - Check if SM-2 algorithm updates the next review date

---

## Step 5: Test Document Upload

1. **Create a test PDF** or use any PDF file you have

2. **Upload via Frontend:**
   - Go to Upload/Documents section
   - Select your test project
   - Upload the PDF
   - Should see processing...
   - Should show extracted text preview

3. **Verify in Database:**
   ```sql
   SELECT filename, page_count, length(extracted_text) as text_length
   FROM documents
   ORDER BY created_at DESC
   LIMIT 5;
   ```

4. **Check Embeddings Were Created:**
   ```sql
   SELECT source_type, source_id, chunk_index, length(content) as content_length
   FROM embeddings
   WHERE source_type = 'document'
   ORDER BY created_at DESC;
   ```

---

## Step 6: Test Quiz Generation

1. **Go to Quiz page** in frontend

2. **Paste some content** (or use this sample):
   ```
   Photosynthesis is the process by which plants convert light energy into chemical energy.
   The formula is 6CO2 + 6H2O + light → C6H12O6 + 6O2.
   Chloroplasts contain chlorophyll, which captures light energy.
   The process occurs in two stages: light reactions and the Calvin cycle.
   ```

3. **Click "Generate Quiz"**
   - Should generate 5 multiple-choice questions
   - Questions should be saved to database

4. **Verify in Database:**
   ```sql
   SELECT question, difficulty
   FROM quiz_questions
   ORDER BY created_at DESC
   LIMIT 5;
   ```

---

## Step 7: Test Match Quiz

1. **Go to Match Quiz page** in frontend

2. **Option A: Use Existing Flashcards**
   - Check "Use existing flashcards"
   - Click "Generate Match Quiz"
   - Should create match pairs from your flashcards

3. **Option B: Generate from Content**
   - Uncheck "Use existing flashcards"
   - Paste content
   - Click "Generate Match Quiz"
   - Should create term-definition pairs

4. **Verify in Database:**
   ```sql
   SELECT term, definition
   FROM match_pairs
   ORDER BY created_at DESC
   LIMIT 5;
   ```

---

## Step 8: Test RAG Chat

1. **Upload a document** (if you haven't already)

2. **Go to Chat page**

3. **Ask a question about your document:**
   - "What is photosynthesis?"
   - "Explain cell structure"
   - "What are the stages of mitosis?"

4. **Verify:**
   - AI should use context from your documents
   - Response should mention specific details from uploaded docs
   - Check `context_sources` in response

5. **Check Chat History in Database:**
   ```sql
   SELECT role, content, created_at
   FROM chat_messages
   ORDER BY created_at DESC
   LIMIT 10;
   ```

---

## Troubleshooting

### Problem: "Row Level Security policy violation"
**Solution:** RLS is still enabled. Run the disable script again.

### Problem: "Cannot connect to database"
**Solution:**
- Check `.env` file has correct Supabase credentials
- Verify backend server is running
- Check Supabase dashboard is accessible

### Problem: "No flashcards found"
**Solution:** Run `test_database.py` again to create test data

### Problem: "Quiz generation failed"
**Solution:**
- Check Gemini API key is valid
- Check backend logs for errors
- Verify `project_id` is being sent in request

### Problem: "Embeddings not created"
**Solution:**
- Check Gemini API key
- Look for errors in backend console
- Verify `embeddings_service_supabase.py` is working

---

## Quick Database Queries for Testing

### Count all data:
```sql
SELECT
  (SELECT COUNT(*) FROM projects) as projects,
  (SELECT COUNT(*) FROM notes) as notes,
  (SELECT COUNT(*) FROM documents) as documents,
  (SELECT COUNT(*) FROM flashcards) as flashcards,
  (SELECT COUNT(*) FROM quiz_questions) as quiz_questions,
  (SELECT COUNT(*) FROM match_pairs) as match_pairs,
  (SELECT COUNT(*) FROM chat_messages) as chat_messages,
  (SELECT COUNT(*) FROM embeddings) as embeddings;
```

### View latest activity:
```sql
SELECT
  'project' as type, name as title, created_at
FROM projects
UNION ALL
SELECT
  'note' as type, title, created_at
FROM notes
UNION ALL
SELECT
  'flashcard' as type, front as title, created_at
FROM flashcards
ORDER BY created_at DESC
LIMIT 20;
```

### Check due flashcards:
```sql
SELECT front, next_review_date,
  CASE
    WHEN next_review_date <= NOW() THEN 'DUE NOW'
    ELSE 'FUTURE'
  END as status
FROM flashcards
ORDER BY next_review_date;
```

---

## Success Checklist

- [ ] RLS disabled in Supabase
- [ ] Test script created project, notes, and flashcards
- [ ] Frontend shows test project
- [ ] Can see notes in frontend
- [ ] Can review flashcards (3 due for review)
- [ ] Can upload PDF document
- [ ] Document text extracted and saved
- [ ] Embeddings generated for document
- [ ] Can generate quiz from content
- [ ] Quiz questions saved to database
- [ ] Can generate match quiz from flashcards
- [ ] Match pairs saved to database
- [ ] Can chat with AI about documents (RAG)
- [ ] Chat messages saved to database

Once all items are checked, your **Supabase integration is fully working!** 🎉

---

## Next Steps After Testing

1. **Customize test data** - Add your own study content
2. **Test spaced repetition** - Review flashcards over multiple days
3. **Upload real PDFs** - Test with actual study materials
4. **Generate real quizzes** - Test learning with your content
5. **Use RAG chat** - Ask questions about your documents
6. **Check analytics** - Use the database views for insights

**For production:**
- Re-enable RLS
- Set up proper authentication
- Use ANON_KEY instead of SERVICE_KEY
- Configure CORS properly
