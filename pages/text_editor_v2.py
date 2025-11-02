"""
Notiq Text Editor - UI Layer
This file contains ONLY Streamlit UI code. All business logic is in interactions/
"""
import json
import os
from datetime import datetime
from typing import List, Dict

import streamlit as st
from streamlit_quill import st_quill
from dotenv import load_dotenv

# Import business logic from interactions
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from interactions import (
    FlashcardGenerator, 
    QuizGenerator, 
    NoteSummarizer,
    get_session_snapshot,
    pack_for_download
)

# Load environment
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    st.warning("GEMINI_API_KEY not found in environment. Set it in your .env file.")

# ──────────────────────────────────────────────────────────────────────────────
# App setup
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Notiq Main Text Editor", page_icon="📝", layout="wide")
st.title("📝 Notiq Text Editor (Streamlit + Quill)")

# ===== State bootstrap =====
if "doc" not in st.session_state:
    st.session_state.doc = ""
if "images" not in st.session_state:
    st.session_state.images = []
if "pdfs" not in st.session_state:
    st.session_state.pdfs = []

# ===== Sidebar =====
with st.sidebar:
    st.header("Save options")
    default_name = datetime.now().strftime("notes-%Y%m%d-%H%M%S")
    filename = st.text_input("Filename (without extension)", value=default_name)
    fmt = st.selectbox("Format", ["markdown (.md)", "json (.json)"], index=0)
    subject = st.text_input("Subject", value="General")

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

# ===== Attachment manager =====
st.markdown("### Manage Attachments")

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

# ===== Save/Download buttons =====
col1, col2, col3 = st.columns([1, 1, 1], vertical_alignment="center")

with col1:
    if st.button("💾 Save"):
        content_str, mime, dl_name = pack_for_download(
            st.session_state.doc,
            st.session_state.images,
            st.session_state.pdfs,
            subject,
            as_json=("json" in fmt)
        )
        with open(dl_name, "w", encoding="utf-8") as f:
            f.write(content_str)
        st.success(f"Saved to {dl_name}")

with col2:
    content_str, mime, dl_name = pack_for_download(
        st.session_state.doc,
        st.session_state.images,
        st.session_state.pdfs,
        subject,
        as_json=("json" in fmt)
    )
    st.download_button("⬇️ Download", content_str, file_name=dl_name, mime=mime)

with col3:
    if st.button("😈 RENDER REALLY COOL LAYOUT"):
        st.info("Coming soon!")

st.caption("Tip: Toggle 'Format' to save as Markdown or JSON. JSON includes embedded attachments.")

# ──────────────────────────────────────────────────────────────────────────────
# Popup rendering helper
# ──────────────────────────────────────────────────────────────────────────────
def show_content_popup(content_md: str, title: str, session_key: str, regenerate_fn=None):
    """
    Generic popup for displaying generated content (summaries, flashcards, quizzes).
    """
    def _render_body():
        st.markdown(f"### {title}")
        st.caption("Auto-generated from your note, images, and PDFs. Refine as you like!")

        effective_content = st.session_state.get(session_key, content_md)

        tabs = st.tabs(["🖼️ Formatted", "🧾 Raw Markdown"])
        with tabs[0]:
            st.markdown(effective_content)
        with tabs[1]:
            st.text_area("Markdown", effective_content, height=500, key=f"{session_key}_raw_view")

        st.divider()
        c1, c2, c3 = st.columns([1, 1, 1])
        
        with c1:
            if st.button("📥 Insert (replace)", key=f"{session_key}_insert"):
                st.session_state.doc = effective_content
                st.toast("Inserted into editor ✍️", icon="✅")
                st.rerun()

        with c2:
            if st.button("➕ Append to editor", key=f"{session_key}_append"):
                existing = st.session_state.get("doc", "")
                st.session_state.doc = (existing + ("\n\n" if existing else "") + effective_content).strip()
                st.toast("Appended to editor ➕", icon="✅")
                st.rerun()

        with c3:
            if regenerate_fn and st.button("🔁 Regenerate", key=f"{session_key}_regen"):
                new_content = regenerate_fn()
                st.session_state[session_key] = new_content
                st.toast("Regenerated 🎲", icon="✨")
                st.rerun()

    # Try different popup methods (version-adaptive)
    if hasattr(st, "dialog") and callable(getattr(st, "dialog")):
        @st.dialog(title)
        def _dlg():
            _render_body()
        _dlg()
    elif hasattr(st, "experimental_dialog") and callable(getattr(st, "experimental_dialog")):
        @st.experimental_dialog(title)
        def _edlg():
            _render_body()
        _edlg()
    elif hasattr(st, "popover"):
        with st.popover(title):
            _render_body()
    else:
        with st.expander(title, expanded=True):
            _render_body()

# ──────────────────────────────────────────────────────────────────────────────
# AI Generation Buttons
# ──────────────────────────────────────────────────────────────────────────────
st.divider()

# Summarize button
if st.button("🪄 Summarize with Gemini", use_container_width=True):
    if not GEMINI_API_KEY:
        st.error("Please set GEMINI_API_KEY in your .env file")
    else:
        snapshot = get_session_snapshot(
            st.session_state.doc,
            st.session_state.images,
            st.session_state.pdfs,
            subject
        )
        with st.spinner("Generating summary..."):
            summarizer = NoteSummarizer(GEMINI_API_KEY)
            summary_md = summarizer.generate(snapshot) or "_No summary generated._"
            st.session_state["last_summary"] = summary_md
            
            def regenerate_summary():
                snap = get_session_snapshot(
                    st.session_state.doc,
                    st.session_state.images,
                    st.session_state.pdfs,
                    subject
                )
                return summarizer.generate(snap) or "_No summary generated._"
            
            show_content_popup(
                summary_md,
                "📚 Session Summary — Notiq",
                "last_summary",
                regenerate_fn=regenerate_summary
            )

# Flashcard button
if st.button("🃏 Generate Flashcards", use_container_width=True):
    if not GEMINI_API_KEY:
        st.error("Please set GEMINI_API_KEY in your .env file")
    else:
        snapshot = get_session_snapshot(
            st.session_state.doc,
            st.session_state.images,
            st.session_state.pdfs,
            subject
        )
        with st.spinner("Generating flashcards..."):
            generator = FlashcardGenerator(GEMINI_API_KEY)
            flashcards_md = generator.generate(snapshot) or "_No flashcards generated._"
            st.session_state["last_flashcards"] = flashcards_md
            
            def regenerate_flashcards():
                snap = get_session_snapshot(
                    st.session_state.doc,
                    st.session_state.images,
                    st.session_state.pdfs,
                    subject
                )
                return generator.generate(snap) or "_No flashcards generated._"
            
            show_content_popup(
                flashcards_md,
                "🃏 Flashcards — Notiq",
                "last_flashcards",
                regenerate_fn=regenerate_flashcards
            )

# Quiz button
if st.button("📝 Generate Quiz", use_container_width=True):
    if not GEMINI_API_KEY:
        st.error("Please set GEMINI_API_KEY in your .env file")
    else:
        snapshot = get_session_snapshot(
            st.session_state.doc,
            st.session_state.images,
            st.session_state.pdfs,
            subject
        )
        with st.spinner("Generating quiz..."):
            generator = QuizGenerator(GEMINI_API_KEY)
            quiz_md = generator.generate(snapshot, num_questions=10) or "_No quiz generated._"
            st.session_state["last_quiz"] = quiz_md
            
            def regenerate_quiz():
                snap = get_session_snapshot(
                    st.session_state.doc,
                    st.session_state.images,
                    st.session_state.pdfs,
                    subject
                )
                return generator.generate(snap, num_questions=10) or "_No quiz generated._"
            
            show_content_popup(
                quiz_md,
                "📝 Quiz — Notiq",
                "last_quiz",
                regenerate_fn=regenerate_quiz
            )

# Debug panel
with st.expander("Debug: session snapshot (JSON)"):
    snapshot = get_session_snapshot(
        st.session_state.doc,
        st.session_state.images,
        st.session_state.pdfs,
        subject
    )
    st.json(snapshot)
