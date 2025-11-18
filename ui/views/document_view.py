# ui/views/document_view.py
import streamlit as st
from datetime import datetime
from supabase_integration.fetching import fetch_document_details

def render_document_view(supabase):
    doc = fetch_document_details(supabase, st.session_state.selected_document)

    if not doc:
        st.error("Document not found")
        if st.button("← Back to Documents"):
            st.session_state.selected_document = None
            st.rerun()
        return

    # Header with back button
    col1, col2 = st.columns([1, 6])
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.selected_document = None
            st.rerun()
    with col2:
        st.title(f"📄 {doc['title']}")

    # Document metadata
    st.markdown(
        f"**Subject:** {doc['subject_folder']} | "
        f"**Created:** {datetime.fromisoformat(doc['created_at']).strftime('%B %d, %Y at %H:%M')}"
    )

    # Key terms chips
    if doc.get('key_terms'):
        st.markdown("**Keywords:**")
        keywords_html = " ".join([
            f'<span style="background-color: #e0e0e0; padding: 5px 10px; border-radius: 15px; margin: 5px; display: inline-block;">{term}</span>'
            for term in doc['key_terms'].split(",")
        ])
        st.markdown(keywords_html, unsafe_allow_html=True)

    st.markdown("---")

    tab1, tab2 = st.tabs(["📝 Clean Text", "✨ Smart Template"])

    with tab1:
        st.markdown("### Clean Text")

        if doc.get('short_summary'):
            st.info(f"**Summary:** {doc['short_summary']}")

        # Images
        if doc.get('images'):
            st.markdown("### 🖼️ Images")
            cols = st.columns(3)
            for idx, img in enumerate(doc['images']):
                with cols[idx % 3]:
                    st.image(
                        img['url'],
                        caption=f"Page {img['page_number']}, Image {img['image_index']}",
                        use_container_width=True
                    )
            st.markdown("---")

        st.markdown("### Content")
        if doc.get('clean_text'):
            st.markdown(doc['clean_text'])
        else:
            st.markdown(doc.get('markdown', 'No content available'))

    with tab2:
        st.markdown("### ✨ Smart Template")
        st.info("🚧 Smart template generation coming soon! This will use AI to create interactive study materials.")
        st.markdown("""
        **Coming soon:**
        - 📊 Interactive flashcards
        - 🧠 Quiz generation
        - 🔗 Concept maps
        - 📈 Study progress tracking
        """)

        if doc.get('clean_text'):
            st.markdown("#### Preview Content")
            st.markdown(doc['clean_text'])
