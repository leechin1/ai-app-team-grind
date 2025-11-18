# ui/views/welcome_view.py
import streamlit as st
from supabase_integration.fetching import get_subject_folders

def render_welcome_view(supabase, logger):
    st.title("📚 Welcome to Notiq")
    st.markdown("### Your intelligent note-taking companion")

    st.markdown("""
    👈 **Get started by selecting a subject from the sidebar**
    
    Or create a new subject to organize your notes!
    
    ---
    
    ### ✨ Features
    - 📁 Organize notes by subject
    - 🖼️ Automatic image extraction from PDFs
    - 🤖 AI-powered summaries and key terms
    - ✨ Smart templates for better studying
    - 🔍 Easy search and navigation
    """)

    try:
        subjects = get_subject_folders(supabase)
        total_docs_response = supabase.table("regular_doc").select("id", count="exact").execute()
        total_docs = total_docs_response.count if total_docs_response.count else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📚 Total Subjects", len(subjects))
        with col2:
            st.metric("📄 Total Documents", total_docs)
        with col3:
            avg_docs = round(total_docs / len(subjects), 1) if subjects else 0
            st.metric("📊 Avg Docs/Subject", avg_docs)
    except Exception as e:
        logger.error(f"Error loading statistics: {e}")
