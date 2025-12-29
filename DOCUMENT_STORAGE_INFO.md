# Document Storage in Supabase

## Current Implementation

Your app currently **extracts and stores text only** from uploaded PDFs:

### What Gets Saved:
- ✅ **Extracted text** → `documents.extracted_text` column
- ✅ **Filename** → `documents.filename`
- ✅ **File size** → `documents.file_size`
- ✅ **MIME type** → `documents.mime_type`
- ✅ **Page count** → `documents.page_count`
- ✅ **Embeddings** → Generated from text, saved to `embeddings` table
- ❌ **Actual PDF file** → NOT stored

### Current Flow:
```
User uploads PDF
    ↓
Backend extracts text using PyPDF2
    ↓
Saves text + metadata to database
    ↓
Generates embeddings from text
    ↓
PDF file is discarded (not stored)
```

---

## Why Text-Only Storage?

**Advantages:**
- ✅ **Faster** - No large file uploads to storage
- ✅ **Cheaper** - Text takes much less space than PDFs
- ✅ **Searchable** - Text is indexed and searchable
- ✅ **RAG-ready** - Embeddings work directly with text
- ✅ **No storage limits** - PostgreSQL text columns can be very large

**Disadvantages:**
- ❌ Cannot download original PDF later
- ❌ Loses formatting/images
- ❌ Cannot re-process with different settings

---

## Option: Add Full File Storage

If you want to store the actual PDF files, here's how:

### 1. Enable Supabase Storage

In Supabase Dashboard:
1. Go to **Storage**
2. Create a bucket called `documents`
3. Set access policies (public or private)

### 2. Update Backend Code

Modify `backend/main.py` document upload endpoint:

```python
@app.post("/api/documents/upload")
async def upload_document(
    project_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """Upload document with FULL file storage"""
    try:
        # Read file
        content = await file.read()

        # 1. UPLOAD TO SUPABASE STORAGE (NEW!)
        file_path = f"{user['id']}/{project_id}/{file.filename}"
        storage_response = db.client.storage.from_('documents').upload(
            file_path,
            content,
            {
                'content-type': file.content_type,
                'x-upsert': 'true'  # Overwrite if exists
            }
        )

        # Get public URL
        public_url = db.client.storage.from_('documents').get_public_url(file_path)

        # 2. Extract text (as before)
        processor = DocumentProcessor(gemini_api_key=os.getenv("GEMINI_API_KEY"))
        processed = processor.process_document(
            file_bytes=content,
            filename=file.filename,
            mime_type=file.content_type
        )

        # 3. Save to database (with storage URL)
        doc_data = DocumentCreate(
            project_id=project_id,
            filename=file.filename,
            file_path=public_url,  # ← Supabase Storage URL
            file_size=len(content),
            mime_type=file.content_type,
            extracted_text=processed.content,
            page_count=processed.metadata.num_pages
        )
        document = await db.create_document(user["id"], doc_data)

        # 4. Generate embeddings (as before)
        # ... rest of code
```

### 3. Benefits of Full Storage

- ✅ Can download original PDF
- ✅ Can re-process later
- ✅ Preserves formatting/images
- ✅ Better for legal/archival purposes

---

## Current Recommendation

**For your use case (study app), text-only storage is perfect because:**

1. **You only need the content** for:
   - RAG (semantic search)
   - Flashcard generation
   - Quiz generation
   - Chat context

2. **Users can always re-upload** if they need the PDF again

3. **Much cheaper and faster** than storing full files

---

## File Size Limits

### Current (Text-only):
- PostgreSQL `text` column: **Up to 1GB** per document
- Effectively unlimited for extracted text

### With Supabase Storage:
- Free tier: **1GB total storage**
- Pro tier: **100GB included**
- File size limit: **50MB per file** (configurable)

---

## Testing Document Upload

After running the test script, you can upload a PDF:

```bash
# Upload a test PDF
curl -X POST "http://localhost:8000/api/documents/upload?project_id=YOUR_PROJECT_ID" \
  -F "file=@path/to/test.pdf"
```

The response will include:
- `extracted_text` - Full text content
- `preview` - First 500 characters
- `metadata.num_pages` - Page count
- `metadata.file_size` - Size in bytes

---

## What Happens to Uploaded Files?

```
┌─────────────┐
│ Upload PDF  │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ Extract Text        │ ← PyPDF2 reads PDF
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Save to Database    │ ← Text + metadata saved
│ - extracted_text    │
│ - filename          │
│ - file_size         │
│ - page_count        │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Generate Embeddings │ ← Gemini creates vectors
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Save Embeddings     │ ← Vectors stored for RAG
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ PDF Discarded       │ ← Original file not stored
└─────────────────────┘
```

---

## Summary

**Current Setup:**
- ✅ **Text extraction** works perfectly
- ✅ **Embeddings** generated automatically
- ✅ **RAG** works with vector search
- ✅ **Fast and cheap** text storage
- ❌ **PDF files** not stored

**If you need full file storage:**
- Follow the "Add Full File Storage" section above
- Enable Supabase Storage bucket
- Update upload endpoint to save to storage
- Files will be accessible via public URLs

For most study app use cases, **text-only storage is recommended** and is what's currently implemented.
