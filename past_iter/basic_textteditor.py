import json
from datetime import datetime
from io import StringIO

import streamlit as st
from streamlit_quill import st_quill

st.set_page_config(page_title="Notiq Main Text Editor", page_icon="📝", layout="wide")

st.title("📝 Notiq Text Editor (Streamlit + Quill)")

# ----- State bootstrap -----
# We'll keep the live document content in a Python variable (session_state).
if "doc" not in st.session_state:
    st.session_state.doc = ""  # this will hold the editor's latest value



with st.sidebar:
    st.header("Save options")
    default_name = datetime.now().strftime("notes-%Y%m%d-%H%M%S") # Update this to available supabase index
    filename = st.text_input("Filename (without extension)", value=default_name)
    fmt = st.selectbox("Format", ["markdown (.md)", "json (.json)"], index=0)
    subject = st.text_input("Subject", value="General")  # Update this to available supabase index
    flashcards = st.text_input("😈 GENERATE FLASHCARDS", value = "This is a fake button")
    quizz = st.text_input("😈 GENERATE QUIZZ", value = "This is a fake button")
    # autosave = st.checkbox("Autosave on every change", value=False)

"""
Potential adds:
- Integrate with Supabase to save notes directly to a database.
- Option to automatically render to smart template and save it to Supabase.
- Subject specific choice
- Better UI/UX
"""

st.markdown(
    """
    yap yap This editor uses **Quill** under the hood, providing formatting similar to Google Docs:
    Bold, italic, underline, headings, lists, links, quotes, code, and more.
    """
)

# ----- Editor -----
# We are working on a session based system, where the file is constantly being overwritten.
# The `value` arg is the initial content; the return value is the current content.
content = st_quill(
    value=st.session_state.doc,
    placeholder="Start typing…",
    html=False,      # Keep as Quill delta/markdown-like text; you can set True to get HTML
    key="quill_editor",
)

# Keep our Python variable up to date
st.session_state.doc = content or ""

# Show what's in the Python variable so you can see it's tracked locally.
with st.expander("Debug: show Python variable (session_state.doc)"):
    st.write(st.session_state.doc)

# ----- Saving helpers -----
def save_to_disk(text: str, as_json: bool):
    base = filename.strip() or "notes"
    path = f"{base}.json" if as_json else f"{base}.md"
    with open(path, "w", encoding="utf-8") as f:
        if as_json:
            json.dump({"content": text, "saved_at": datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
        else:
            f.write(text)
    return path

col1, col2, col3 = st.columns([1,1,1], vertical_alignment="center")
with col1:
    if st.button("💾 Save"):
        saved_path = save_to_disk(st.session_state.doc, as_json=("json" in fmt))
        st.success(f"Saved to {saved_path}")

with col2:
    # Offer a client-side download too
    if "json" in fmt:
        payload = json.dumps({"content": st.session_state.doc, "saved_at": datetime.now().isoformat()}, ensure_ascii=False, indent=2)
        mime = "application/json"
        dl_name = f"{filename or 'notes'}.json"
    else:
        payload = st.session_state.doc
        mime = "text/markdown"
        dl_name = f"{filename or 'notes'}.md"
    st.download_button("⬇️ Download", payload, file_name=dl_name, mime=mime)

with col3:
    if st.button("😈 RENDER REALLY COOL LAYOUT"):
        print("")

st.caption("Tip: Toggle 'Format' to save as Markdown or JSON. The live content is always in `st.session_state.doc`.")
e