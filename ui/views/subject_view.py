# ui/views/subject_view.py
import streamlit as st
from datetime import datetime
from supabase_integration.fetching import (
    fetch_documents_by_subject,
    get_subject_folders,
)

def render_subject_view(supabase, logger):
    subject = st.session_state.selected_subject

    st.title(f"📁 {subject}")
    st.markdown("---")

    documents = fetch_documents_by_subject(supabase, subject)
    logger.info(f"Displaying {len(documents)} documents for '{subject}'")

    if not documents:
        st.info(f"No documents in '{subject}' yet. Upload your first document!")

        with st.expander("🔍 Debug Info"):
            st.write(f"Looking for documents where subject_folder = '{subject}'")

            all_subjects = get_subject_folders(supabase)
            st.write(f"Available subjects: {all_subjects}")

            all_docs = supabase.table("regular_doc").select("subject_folder").execute()
            unique_folders = list({d['subject_folder'] for d in all_docs.data})
            st.write(f"Unique subject_folder values in documents: {unique_folders}")
        return

    st.markdown(f"### 📚 {len(documents)} Documents")

    for doc in documents:
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])

            with col1:
                st.markdown(f"### 📄 {doc['title']}")
                if doc.get('short_summary'):
                    st.caption(doc['short_summary'])

            with col2:
                if doc.get('key_terms'):
                    st.markdown("**Keywords:**")
                    for term in doc['key_terms'].split(","):
                        st.caption(f"🏷️ {term}")

            with col3:
                created_date = datetime.fromisoformat(doc['created_at'])
                st.caption(f"📅 {created_date.strftime('%b %d, %Y')}")

                if doc.get('images'):
                    st.caption(f"🖼️ {len(doc['images'])} images")

                if st.button("Open →", key=f"open_doc_{doc['id']}", use_container_width=True):
                    st.session_state.selected_document = doc['id']
                    st.rerun()

            st.markdown("---")
