import json
import base64
import mimetypes
import re
import time
import uuid
from datetime import datetime

import streamlit as st
from streamlit_quill import st_quill

# --- Supabase client ---
# pip install supabase
from supabase import create_client, Client

# ------------------ Streamlit page setup ------------------
st.set_page_config(page_title="Notiq Main Text Editor", page_icon="📝", layout="wide")
st.title("📝 Notiq Text Editor (Streamlit + Quill)")

# ------------------ Supabase config ------------------
# Put these in .streamlit/secrets.toml:
# SUPABASE_URL = "https://xxxx.supabase.co"
# SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6..."
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_ANON_KEY", "")
if not SUPABASE_URL or not SUPABASE_KEY:
    st.warning("Supabase URL/Key not found in st.secrets. Add SUPABASE_URL and SUPABASE_ANON_KEY.")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

BUCKET = "notes-media"  # create this bucket in Supabase Storage (public or private as you prefer)

# ------------------ Session bootstrap ------------------
# We'll keep the live document content in a Python variable (session_state).
# Use a Quill Delta dict as the canonical representation.
if "doc" not in st.session_state:
    st.session_state.doc = {"ops": []}  # Quill Delta

# ------------------ Sidebar (save options) ------------------
with st.sidebar:
    st.header("Save options")
    default_name = datetime.now().strftime("notes-%Y%m%d-%H%M%S")  # e.g. notes-20250101-121314
    filename = st.text_input("Title", value=default_name)
    subject = st.text_input("Subject", value="General")
    st.caption("Notes are saved as **Quill Delta (JSON)** in Supabase. Images are uploaded to Supabase Storage.")
    st.divider()
    flashcards = st.text_input("😈 GENERATE FLASHCARDS", value="This is a fake button")
    quizz = st.text_input("😈 GENERATE QUIZZ", value="This is a fake button")

st.markdown(
    """
    This editor uses **Quill** under the hood, providing formatting similar to Google Docs:
    bold, italic, underline, headings, lists, links, quotes, code, and more.
    """
)

# ------------------ Editor ------------------
# The `value` arg is the initial content; the return value is the current Delta (dict) when html=False.
delta = st_quill(
    value=st.session_state.get("doc") or {"ops": []},
    placeholder="Start typing…",
    html=False,   # keep as Quill Delta
    key="quill_editor",
)

# Ensure doc is a Delta dict (streamlit_quill may return None on first render).
st.session_state.doc = delta or {"ops": []}

# Debug panel to see the live delta
with st.expander("Debug: show Python variable (session_state.doc)"):
    st.json(st.session_state.doc)

# ------------------ Image handling + Supabase helpers ------------------
dataurl_re = re.compile(r"^data:(?P<mime>[^;]+);base64,(?P<b64>.+)$")

def upload_data_url_to_storage(data_url: str, note_id: str) -> str:
    """
    Takes a data URL, uploads to Supabase Storage, returns a public (or signed) URL.
    If it's already a URL, pass it through.
    """
    if not supabase:
        # If Supabase isn't configured, just return the original (so you can still test the editor)
        return data_url

    m = dataurl_re.match(data_url)
    if not m:
        return data_url  # already a URL

    mime = m.group("mime")
    raw = base64.b64decode(m.group("b64"))
    ext = mimetypes.guess_extension(mime) or ".bin"

    # Path pattern: notes/<note_id>/<timestamp>-<rand>.ext
    path = f"notes/{note_id}/{int(time.time())}-{uuid.uuid4().hex}{ext}"

    # Upload to Storage; for private buckets, consider using create_signed_url for rendering
    supabase.storage.from_(BUCKET).upload(path, raw, {"content-type": mime})

    # Public URL (change to create_signed_url if your bucket is private)
    public_url = supabase.storage.from_(BUCKET).get_public_url(path)
    return public_url

def externalize_images_in_delta(delta_obj: dict, note_id: str) -> dict:
    """
    Replace any base64 image embeds in the Quill Delta with Supabase Storage URLs.
    Returns a new Delta dict.
    """
    new_delta = {"ops": []}
    for op in (delta_obj.get("ops") or []):
        new_op = dict(op)
        ins = new_op.get("insert")
        if isinstance(ins, dict) and "image" in ins:
            new_op["insert"] = dict(ins)  # copy nested dict
            new_op["insert"]["image"] = upload_data_url_to_storage(ins["image"], note_id)
        new_delta["ops"].append(new_op)
    return new_delta

def save_note_to_supabase(delta_obj: dict, title: str, subject: str):
    """
    1) Generate a note_id
    2) Upload any base64 images to Storage, rewrite Delta to use URLs
    3) Insert row into 'notes' table with JSONB content
    """
    note_id = str(uuid.uuid4())
    clean_delta = externalize_images_in_delta(delta_obj, note_id)

    if not supabase:
        # Let the app keep working even when Supabase isn't configured
        return note_id, clean_delta, None

    payload = {
        "id": note_id,
        "title": title.strip() or "Untitled",
        "subject": subject.strip() or None,
        "format": "quill-delta",
        "content": clean_delta,
        "html_cached": None,  # optional: compute and store an HTML render
    }
    res = supabase.table("notes").insert(payload).execute()
    return note_id, clean_delta, res

def save_to_disk_as_json(delta_obj: dict, base: str):
    """Optional local save of the Delta JSON (good for quick backups)."""
    path = f"{(base or 'notes').strip()}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"content": delta_obj, "saved_at": datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
    return path

# ------------------ Actions ------------------
col1, col2, col3 = st.columns([1, 1, 1], vertical_alignment="center")

with col1:
    if st.button("💾 Save to Supabase", type="primary"):
        try:
            note_id, clean_delta, res = save_note_to_supabase(st.session_state.doc, filename, subject)
            st.success(f"Saved to Supabase as note {note_id}")
            # Update in-memory doc to the cleaned version (with image URLs instead of base64)
            st.session_state.doc = clean_delta
        except Exception as e:
            st.error(f"Save failed: {e}")

with col2:
    # Client-side download of the **Delta JSON** (source of truth)
    payload = json.dumps(
        {"content": st.session_state.doc, "saved_at": datetime.now().isoformat()},
        ensure_ascii=False, indent=2
    )
    dl_name = f"{(filename or 'notes').strip()}.json"
    st.download_button("⬇️ Download (Delta JSON)", payload, file_name=dl_name, mime="application/json")

with col3:
    if st.button("😈 RENDER REALLY COOL LAYOUT"):
        # Placeholder for your custom renderer / template pipeline
        st.info("Coming soon: render to a smart template and save preview HTML to Supabase.")

st.caption(
    "Notes are stored as **Quill Delta (JSON)**. Images are uploaded to **Supabase Storage** and referenced by URL. "
    "This is the most reliable round-trip with Quill and compatible with Supabase (JSONB + Storage)."
)
