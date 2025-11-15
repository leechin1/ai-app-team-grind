# main.py
import streamlit as st
from dotenv import load_dotenv
import logging
from datetime import datetime
from supabase_integration.fetching import (
    init_supabase,
    get_subject_folders,
    fetch_documents_by_subject,
    fetch_document_details,
    create_new_subject,
    debug_cache_info
)

# Load environment variables
load_dotenv()

# Initialize Supabase
supabase = init_supabase()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configure page
st.set_page_config(
    page_title="Notiq - My Notes",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session states
if 'selected_subject' not in st.session_state:
    st.session_state.selected_subject = None
if 'selected_document' not in st.session_state:
    st.session_state.selected_document = None
if 'show_new_subject_dialog' not in st.session_state:
    st.session_state.show_new_subject_dialog = False

# Sidebar - Subject Navigation
with st.sidebar:
    st.title("📚 My Subjects")
    st.markdown("---")
    
    # Get all subjects
    subjects = get_subject_folders(supabase)
    
    if not subjects:
        st.warning("No subjects found. Create your first subject!")
    else:
        # Display subjects as buttons
        st.markdown("### 📂 Folders")
        for subject in subjects:
            # Create a button for each subject
            if st.button(
                f"📁 {subject}", 
                key=f"subject_{subject}",
                use_container_width=True,
                type="primary" if st.session_state.selected_subject == subject else "secondary"
            ):
                st.session_state.selected_subject = subject
                st.session_state.selected_document = None  # Clear document selection
                st.rerun()
    
    st.markdown("---")
    
    # Debug cache info (optional - remove in production)
    debug_cache_info()
    
    st.markdown("---")
    
    # New Subject Button
    if st.button("➕ New Subject", use_container_width=True, type="primary"):
        st.session_state.show_new_subject_dialog = True
        st.rerun()
    
    # New Subject Dialog
    if st.session_state.show_new_subject_dialog:
        st.markdown("### Create New Subject")
        new_subject_name = st.text_input("Subject Name", key="new_subject_input")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Create", type="primary", use_container_width=True):
                if new_subject_name:
                    success, message = create_new_subject(supabase, new_subject_name)
                    if success:
                        st.success(message)
                        st.session_state.show_new_subject_dialog = False
                        st.session_state.selected_subject = new_subject_name
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Please enter a subject name")
        
        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.show_new_subject_dialog = False
                st.rerun()

# Main Content Area
if st.session_state.selected_document is not None:
    # DOCUMENT VIEW MODE
    doc = fetch_document_details(supabase, st.session_state.selected_document)
    
    if doc:
        # Header with back button
        col1, col2 = st.columns([1, 6])
        with col1:
            if st.button("← Back", use_container_width=True):
                st.session_state.selected_document = None
                st.rerun()
        with col2:
            st.title(f"📄 {doc['title']}")
        
        # Document metadata
        st.markdown(f"**Subject:** {doc['subject_folder']} | **Created:** {datetime.fromisoformat(doc['created_at']).strftime('%B %d, %Y at %H:%M')}")
        
        # Key terms chips
        if doc.get('key_terms') and len(doc['key_terms']) > 0:
            st.markdown("**Keywords:**")
            keywords_html = " ".join([f'<span style="background-color: #e0e0e0; padding: 5px 10px; border-radius: 15px; margin: 5px; display: inline-block;">{term}</span>' for term in doc['key_terms'].split(",")])
            st.markdown(keywords_html, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Tabs for different views
        tab1, tab2 = st.tabs(["📝 Clean Text", "✨ Smart Template"])
        
        with tab1:
            st.markdown("### Clean Text")
            
            # Short summary in an info box
            if doc.get('short_summary'):
                st.info(f"**Summary:** {doc['short_summary']}")
            
            # Display images if available
            if doc.get('images') and len(doc['images']) > 0:
                st.markdown("### 🖼️ Images")
                
                # Display images in a grid
                cols = st.columns(3)
                for idx, img in enumerate(doc['images']):
                    with cols[idx % 3]:
                        st.image(img['url'], caption=f"Page {img['page_number']}, Image {img['image_index']}", use_container_width=True)
                
                st.markdown("---")
            
            # Main content
            st.markdown("### Content")
            if doc.get('clean_text'):
                st.markdown(doc['clean_text'])
            else:
                st.markdown(doc.get('markdown', 'No content available'))
        
        with tab2:
            st.markdown("### ✨ Smart Template")
            st.info("🚧 Smart template generation coming soon! This will use AI to create interactive study materials.")
            
            # Placeholder for future smart template features
            st.markdown("""
            **Coming soon:**
            - 📊 Interactive flashcards
            - 🧠 Quiz generation
            - 🔗 Concept maps
            - 📈 Study progress tracking
            """)
            
            # For now, show a structured version of the content
            if doc.get('clean_text'):
                st.markdown("#### Preview Content")
                st.markdown(doc['clean_text'])
    
    else:
        st.error("Document not found")
        if st.button("← Back to Documents"):
            st.session_state.selected_document = None
            st.rerun()

elif st.session_state.selected_subject:
    # DOCUMENTS LIST VIEW MODE
    st.title(f"📁 {st.session_state.selected_subject}")
    st.markdown("---")
    
    # Fetch documents for selected subject
    documents = fetch_documents_by_subject(supabase, st.session_state.selected_subject)
    
    logger.info(f"Displaying {len(documents)} documents for '{st.session_state.selected_subject}'")
    
    if not documents:
        st.info(f"No documents in '{st.session_state.selected_subject}' yet. Upload your first document!")
        
        # Debug section
        with st.expander("🔍 Debug Info"):
            st.write(f"Looking for documents where subject_folder = '{st.session_state.selected_subject}'")
            
            # Show all subjects in database
            all_subjects = get_subject_folders(supabase)
            st.write(f"Available subjects: {all_subjects}")
            
            # Show all unique subject_folder values in documents
            all_docs = supabase.table("regular_doc").select("subject_folder").execute()
            unique_folders = list(set([d['subject_folder'] for d in all_docs.data]))
            st.write(f"Unique subject_folder values in documents: {unique_folders}")
    else:
        st.markdown(f"### 📚 {len(documents)} Documents")
        
        # Display documents as cards
        for doc in documents:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.markdown(f"### 📄 {doc['title']}")
                    if doc.get('short_summary'):
                        st.caption(doc['short_summary'])
                
                with col2:
                    # Display keywords as pills
                    if doc.get('key_terms') and len(doc['key_terms']) > 0:
                        st.markdown("**Keywords:**")
                        for term in doc['key_terms'].split(","):  # Show first 3
                            st.caption(f"🏷️ {term}")
                        
                
                with col3:
                    created_date = datetime.fromisoformat(doc['created_at'])
                    st.caption(f"📅 {created_date.strftime('%b %d, %Y')}")
                    
                    # Image count badge
                    if doc.get('images') and len(doc['images']) > 0:
                        st.caption(f"🖼️ {len(doc['images'])} images")
                    
                    # Open button
                    if st.button("Open →", key=f"open_doc_{doc['id']}", use_container_width=True):
                        st.session_state.selected_document = doc['id']
                        st.rerun()
                
                st.markdown("---")

else:
    # WELCOME SCREEN
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
    
    # Show statistics
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