import json
import base64
from datetime import datetime
from typing import List, Dict
import os

import streamlit as st
from streamlit_quill import st_quill

# ==== Gemini SDK ====
from google import genai
from google.genai import types
from dotenv import load_dotenv

# ==== Import our study tools ====
import sys
from pathlib import Path
# Add parent directory to path so we can import gemini_tools
sys.path.insert(0, str(Path(__file__).parent.parent))
from gemini_tools import FlashcardGenerator, QuizGenerator


# Load environment + client
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    st.warning("GEMINI_API_KEY not found in environment. Set it in your .env file.")

#from llm_helper import *

# ──────────────────────────────────────────────────────────────────────────────
# App setup
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Notiq Main Text Editor", page_icon="📝", layout="wide")
st.title("📝 Notiq Text Editor (Streamlit + Quill)")

# ===== State bootstrap =====
if "doc" not in st.session_state:
    st.session_state.doc = ""  # editor's latest value

# Attachment state
# Each item is a dict: {"name": str, "mime": str, "bytes": bytes, "caption": str}
if "images" not in st.session_state:
    st.session_state.images: List[Dict] = []
if "pdfs" not in st.session_state:
    st.session_state.pdfs: List[Dict] = []

with st.sidebar:
    st.header("Save options")
    default_name = datetime.now().strftime("notes-%Y%m%d-%H%M%S")  # can map to supabase index
    filename = st.text_input("Filename (without extension)", value=default_name)
    fmt = st.selectbox("Format", ["markdown (.md)", "json (.json)"], index=0)
    subject = st.text_input("Subject", value="General")  # can map to supabase index

st.markdown("This editor uses **Quill** under the hood (Google Docs–style formatting).")

# ===== Editor =====
content = st_quill(
    value=st.session_state.doc,
    placeholder="Start typing…",
    html=False,
    key="quill_editor",
)
st.session_state.doc = content or ""

with st.expander("Debug: show Python variable (session_state.doc)"):
    st.write(st.session_state.doc)

# ===== Attachments: Images & PDFs =====
st.subheader("📎 Attachments")
st.caption("Tip: You can **drag & drop** files here or **paste** an image with Ctrl/Cmd + V while this page is focused.")
col_img, col_pdf = st.columns(2)

with col_img:
    st.markdown("#### 🖼️ Images")
    up_images = st.file_uploader(
        "Upload or paste images",
        type=["png", "jpg", "jpeg", "gif", "bmp", "tiff", "webp"],
        accept_multiple_files=True,
        key="uploader_images",
        help="Drag & drop or paste (Ctrl/Cmd+V) images here.",
    )
    if up_images:
        for f in up_images:
            exists = any((f.name == it["name"] and f.size == len(it["bytes"])) for it in st.session_state.images)
            if not exists:
                st.session_state.images.append(
                    {"name": f.name, "mime": f.type or "image/*", "bytes": f.read(), "caption": ""}
                )

with col_pdf:
    st.markdown("#### 📄 PDFs")
    up_pdfs = st.file_uploader(
        "Upload PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        key="uploader_pdfs",
        help="Drag & drop PDF files here.",
    )
    if up_pdfs:
        for f in up_pdfs:
            exists = any((f.name == it["name"] and f.size == len(it["bytes"])) for it in st.session_state.pdfs)
            if not exists:
                st.session_state.pdfs.append(
                    {"name": f.name, "mime": f.type or "application/pdf", "bytes": f.read(), "caption": ""}
                )

# ===== Attachment manager (edit captions/titles, remove items) =====
st.markdown("### Manage Attachments")

# Images manager
if st.session_state.images:
    st.write("**Images**")
    for idx, item in enumerate(st.session_state.images):
        with st.container(border=True):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.image(item["bytes"], caption=item.get("caption") or item["name"], use_column_width=True)
            with c2:
                item["name"] = st.text_input(f"Filename (image #{idx+1})", value=item["name"], key=f"img_name_{idx}")
                item["caption"] = st.text_input(f"Caption (image #{idx+1})", value=item.get("caption", ""), key=f"img_caption_{idx}")
                if st.button("🗑️ Remove", key=f"img_remove_{idx}"):
                    st.session_state.images.pop(idx)
                    st.rerun()
else:
    st.info("No images attached yet.")

# PDFs manager
if st.session_state.pdfs:
    st.write("**PDFs**")
    for idx, item in enumerate(st.session_state.pdfs):
        with st.container(border=True):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.write(f"**{item['name']}**")
                st.caption(item.get("caption", ""))
                st.download_button(
                    "⬇️ Download PDF",
                    data=item["bytes"],
                    file_name=item["name"],
                    mime=item["mime"],
                    key=f"pdf_dl_{idx}",
                )
            with c2:
                item["name"] = st.text_input(f"Filename (pdf #{idx+1})", value=item["name"], key=f"pdf_name_{idx}")
                item["caption"] = st.text_input(f"Notes / caption (pdf #{idx+1})", value=item.get("caption", ""), key=f"pdf_caption_{idx}")
                if st.button("🗑️ Remove", key=f"pdf_remove_{idx}"):
                    st.session_state.pdfs.pop(idx)
                    st.rerun()
else:
    st.info("No PDFs attached yet.")

# ===== Saving helpers =====
def save_to_disk(text: str, as_json: bool):
    base = filename.strip() or "notes"
    path = f"{base}.json" if as_json else f"{base}.md"
    if as_json:
        images_serialized = [
            {
                "name": it["name"],
                "mime": it["mime"],
                "caption": it.get("caption", ""),
                "data_b64": base64.b64encode(it["bytes"]).decode("ascii"),
            }
            for it in st.session_state.images
        ]
        pdfs_serialized = [
            {
                "name": it["name"],
                "mime": it["mime"],
                "caption": it.get("caption", ""),
                "data_b64": base64.b64encode(it["bytes"]).decode("ascii"),
            }
            for it in st.session_state.pdfs
        ]
        payload = {
            "subject": subject,
            "content": text,
            "images": images_serialized,
            "pdfs": pdfs_serialized,
            "saved_at": datetime.now().isoformat(),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    return path

col1, col2, col3 = st.columns([1, 1, 1], vertical_alignment="center")
with col1:
    if st.button("💾 Save"):
        saved_path = save_to_disk(st.session_state.doc, as_json=("json" in fmt))
        st.success(f"Saved to {saved_path}")

with col2:
    if "json" in fmt:
        payload = {
            "subject": subject,
            "content": st.session_state.doc,
            "images": [
                {
                    "name": it["name"],
                    "mime": it["mime"],
                    "caption": it.get("caption", ""),
                    "data_b64": base64.b64encode(it["bytes"]).decode("ascii"),
                }
                for it in st.session_state.images
            ],
            "pdfs": [
                {
                    "name": it["name"],
                    "mime": it["mime"],
                    "caption": it.get("caption", ""),
                    "data_b64": base64.b64encode(it["bytes"]).decode("ascii"),
                }
                for it in st.session_state.pdfs
            ],
            "saved_at": datetime.now().isoformat(),
        }
        payload_str = json.dumps(payload, ensure_ascii=False, indent=2)
        mime = "application/json"
        dl_name = f"{filename or 'notes'}.json"
    else:
        payload_str = st.session_state.doc
        mime = "text/markdown"
        dl_name = f"{filename or 'notes'}.md"
    st.download_button("⬇️ Download", payload_str, file_name=dl_name, mime=mime)

with col3:
    if st.button("😈 RENDER REALLY COOL LAYOUT"):
        print("")

st.caption("Tip: Toggle 'Format' to save as Markdown or JSON. JSON includes embedded attachments.")

# Load environment + client
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    st.warning("GEMINI_API_KEY not found in environment. Set it in your .env file.")



# ──────────────────────────────────────────────────────────────────────────────
# Snapshot & Gemini helpers
# ──────────────────────────────────────────────────────────────────────────────
def get_session_snapshot() -> Dict:
    """Return a normalized dict of the current note, with attachments base64-encoded."""
    doc = st.session_state.get("doc", "")

    def _pack(items):
        return [
            {
                "name": it["name"],
                "mime": it["mime"],
                "caption": it.get("caption", ""),
                "data_b64": base64.b64encode(it["bytes"]).decode("ascii"),
            }
            for it in items
        ]

    images = _pack(st.session_state.get("images", []))
    pdfs = _pack(st.session_state.get("pdfs", []))

    return {
        "subject": st.session_state.get("subject", subject),
        "content": doc,
        "images": images,
        "pdfs": pdfs,
        "saved_at": datetime.now().isoformat(),
    }

def build_gemini_contents(snapshot: Dict):
    """
    Build a single user message with mixed parts:
      - Text parts for instructions + note text
      - Inline image parts (base64) so Gemini can inspect them
      - Text list of PDFs (name/caption only)
    """
    header = (
        "You are a study buddy enhancing note-taking layouts into smart formats.\n"
        "Summarize the entire session (notes + images + PDFs), extract key points, action items, definitions, and a clean outline.\n"
        "Return Markdown with:\n"
        "1) Executive summary\n"
        "2) Bullet key takeaways\n"
        "3) Action items (checkbox list)\n"
        "4) Glossary (term → definition)\n"
        "5) References (list attached assets)\n"
        "Keep it concise and well-structured."
    )

    parts = [{"text": header}]

    note_text = snapshot.get("content", "")
    subj = snapshot.get("subject", "General")
    parts.append({"text": f"Subject: {subj}\n\nFull note content:\n{note_text}\n"})

    # Inline images
    for img in snapshot.get("images", []):
        parts.append({"text": f"[Image: {img.get('name','(unnamed)')}] Caption: {img.get('caption','')}"})
        parts.append({
            "inline_data": {
                "mime_type": img.get("mime", "image/*"),
                "data": img.get("data_b64", ""),
            }
        })

    # PDFs (names + captions only)
    if snapshot.get("pdfs"):
        pdf_lines = []
        for p in snapshot["pdfs"]:
            pdf_lines.append(f"- {p.get('name','(unnamed)')} — {p.get('caption','')}".strip())
        parts.append({"text": "Attached PDFs (names & notes only; content not embedded to save tokens):\n" + "\n".join(pdf_lines)})

    parts.append({"text": "Now produce the summary in Markdown."})
    return [{"role": "user", "parts": parts}]



def summarize_with_gemini(snapshot: Dict) -> str:
    client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else genai.Client()
    contents = build_gemini_contents(snapshot)
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction="You are a study buddy enhancing note-taking layouts into smart formats.",
            temperature=0.3,
            max_output_tokens=2048,
        ),
    )
    return (getattr(resp, "text", "") or "").strip()

# ===================== Fancy, version-adaptive popup =========================
def _render_summary_body(summary_md: str, filename_base: str = "session-summary"):
    st.markdown("### ✨ Smart Session Summary")
    st.caption("Auto-generated from your note, images, and PDFs. Refine as you like!")

    # Always reflect the latest regenerated summary if present
    effective_summary = st.session_state.get("last_summary", summary_md)

    tabs = st.tabs(["🖼️ Formatted", "🧾 Raw Markdown"])
    with tabs[0]:
        st.markdown(effective_summary)
    with tabs[1]:
        st.text_area("Markdown", effective_summary, height=500, key="summary_raw_view")

    st.divider()
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        if st.button("📥 Insert (replace)", key="insert_replace"):
            st.session_state.doc = effective_summary
            st.toast("Inserted into editor ✍️", icon="✅")
            st.rerun()

    with c2:
        if st.button("➕ Append to editor", key="insert_append"):
            existing = st.session_state.get("doc", "")
            st.session_state.doc = (existing + ("\n\n" if existing else "") + effective_summary).strip()
            st.toast("Appended to editor ➕", icon="✅")
            st.rerun()

    with c3:
        if st.button("🔁 Regenerate", key="regen_summary"):
            snap = get_session_snapshot()
            new_md = summarize_with_gemini(snap) or "_No summary generated._"
            st.session_state["last_summary"] = new_md
            st.toast("Regenerated 🎲", icon="✨")
            st.rerun()



def show_summary_popup(summary_md: str, title: str = "📚 Session Summary — Notiq", filename_base: str = "session-summary"):
    # Prefer st.dialog (decorator)
    if hasattr(st, "dialog") and callable(getattr(st, "dialog")):
        @st.dialog(title)
        def _dlg():
            _render_summary_body(summary_md, filename_base)
        _dlg()
        return

    # Fallback to st.experimental_dialog (decorator)
    if hasattr(st, "experimental_dialog") and callable(getattr(st, "experimental_dialog")):
        @st.experimental_dialog(title)
        def _edlg():
            _render_summary_body(summary_md, filename_base)
        _edlg()
        return

    # Popover fallback (context manager). Not modal, but styled & scrollable.
    if hasattr(st, "popover"):
        with st.popover(title):
            _render_summary_body(summary_md, filename_base)
        return

    # Last resort: an always-open expander at the top
    with st.expander(title, expanded=True):
        _render_summary_body(summary_md, filename_base)

# ──────────────────────────────────────────────────────────────────────────────
# UI: Summarize button + popup
# ──────────────────────────────────────────────────────────────────────────────
st.divider()
if st.button("🪄 Summarize with Gemini", use_container_width=True):
    snapshot = get_session_snapshot()
    summary_md = summarize_with_gemini(snapshot) or "_No summary generated._"
    st.session_state["last_summary"] = summary_md
    show_summary_popup(summary_md, title="📚 Session Summary — Notiq", filename_base=f"{(subject or 'notes').strip()}-summary")

# NEW: Flashcard button
if st.button("🃏 Generate Flashcards", use_container_width=True):
    if not GEMINI_API_KEY:
        st.error("Please set GEMINI_API_KEY in your .env file")
    else:
        snapshot = get_session_snapshot()
        with st.spinner("Generating flashcards..."):
            generator = FlashcardGenerator(GEMINI_API_KEY)
            flashcards_md = generator.generate(snapshot) or "_No flashcards generated._"
            st.session_state["last_flashcards"] = flashcards_md
            show_summary_popup(
                flashcards_md, 
                title="🃏 Flashcards — Notiq", 
                filename_base=f"{(subject or 'notes').strip()}-flashcards"
            )

# NEW: Quiz button
if st.button("📝 Generate Quiz", use_container_width=True):
    if not GEMINI_API_KEY:
        st.error("Please set GEMINI_API_KEY in your .env file")
    else:
        snapshot = get_session_snapshot()
        with st.spinner("Generating quiz..."):
            generator = QuizGenerator(GEMINI_API_KEY)
            quiz_md = generator.generate(snapshot, num_questions=10) or "_No quiz generated._"
            st.session_state["last_quiz"] = quiz_md
            show_summary_popup(
                quiz_md, 
                title="📝 Quiz — Notiq", 
                filename_base=f"{(subject or 'notes').strip()}-quiz"
            )

# Optional: also expose the raw snapshot for debugging (collapsed)
with st.expander("Debug: session snapshot (JSON)"):
    st.json(get_session_snapshot())
