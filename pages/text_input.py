
import streamlit as st
from dotenv import load_dotenv
import json
import base64
from datetime import datetime
from typing import List, Dict
import os

from streamlit_quill import st_quill

# Import required libraries
from docling.document_converter import DocumentConverter
import logging
from utils.supabase_utils import (
    init_supabase, 
    get_subject_folders, 
    process_uploaded_file, 
    save_to_database
)

# Load environment variables
load_dotenv()

supabase = init_supabase()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configure page
st.set_page_config(
    page_title="Notiq",
    page_icon="🎫",
    layout="wide"
)

# Main header
st.title("Notiq")
st.markdown("Like a study buddy but better")

# Get subject folders from database
SUBJECT_FOLDERS = get_subject_folders(supabase)

# Initialize session state for tab tracking
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = None

# Sidebar with info
with st.sidebar:
    st.header("About")
    st.markdown("""
    Upload a PDF file or write your own text.
    """)

# Single input section for file name and subject (above tabs)
st.markdown("### Document Information")
col1, col2 = st.columns(2)

with col1:
    file_title = st.text_input("File Name", key="global_file_title")

with col2:
    selected_subject = st.selectbox(
        "Subject Folder",
        options=SUBJECT_FOLDERS,
        key='global_subject_selector'
    )

st.markdown("---")

# Main content area
tab1, tab2 = st.tabs(["Text Editor", "Upload PDF"])

with tab1:
    # Check if tab changed and clear Tab 2 state
    if st.session_state.current_tab == 'tab2':
        # Clear PDF-related state
        if 'markdown_content' in st.session_state:
            st.session_state.markdown_content = None
        if 'conversion_complete' in st.session_state:
            st.session_state.conversion_complete = False
        if 'uploaded_file_content' in st.session_state:
            st.session_state.uploaded_file_content = None
    
    st.session_state.current_tab = 'tab1'
    
    st.header("Write your own magic notes")

    # Initialize text editor content
    if "doc" not in st.session_state:
        st.session_state.doc = ""
    
    content = st_quill(
        value=st.session_state.doc,
        placeholder="Start typing…",
        html=False,
        key="quill_editor",
    )
    st.session_state.doc = content or ""

    # Save button for text editor
    st.markdown("---")
    if st.button("💾 Save Notes to Database", type="primary", key='save_text_button'):
        # Validate inputs
        if not file_title:
            st.error("Please enter a file name")
        elif not st.session_state.doc:
            st.error("Please write some content before saving")
        elif not selected_subject:
            st.error("Please select a subject folder")
        else:
            with st.spinner('Saving to database...'):
                # Use utility function to save to database
                success, error_message = save_to_database(
                    supabase,
                    file_title, 
                    selected_subject,
                    st.session_state.doc
                )
                
                if success:
                    st.success(f"✅ Document saved successfully to '{selected_subject}' folder!")
                    st.balloons()
                    
                    # Optionally clear the editor after save
                    st.session_state.doc = ""
                    st.rerun()
                else:
                    st.error(error_message)
                    st.error("Please check your Supabase credentials and table configuration.")

with tab2:
    # Check if tab changed and clear Tab 1 state
    if st.session_state.current_tab == 'tab1':
        # Clear text editor state
        if 'doc' in st.session_state:
            st.session_state.doc = ""
    
    st.session_state.current_tab = 'tab2'
    
    st.header("PDF to Markdown Converter")

    # Initialize the DocumentConverter once per session
    if 'converter' not in st.session_state:
        try:
            st.session_state.converter = DocumentConverter()
            logger.debug("Converter successfully created")
        except Exception as e:
            logger.error(f"Error creating converter: {str(e)}")
            st.error(f"Error creating converter: {str(e)}")
            st.stop()

    # Initialize session state for markdown content and conversion status
    if 'markdown_content' not in st.session_state:
        st.session_state.markdown_content = None
    if 'conversion_complete' not in st.session_state:
        st.session_state.conversion_complete = False

    # File upload widget
    uploaded_file = st.file_uploader(
        "Upload your PDF file",
        type=['pdf'],
        key='pdf_uploader',
        help="Drag and drop or click to select a file (max 200MB)"
    )

    # Convert button
    convert_clicked = st.button("Convert to Markdown", type="primary")

    # Process conversion when button is clicked
    if convert_clicked:
        if uploaded_file is not None:
            # Validate file name
            if not file_title:
                st.error("Please enter a file name before converting")
            elif not selected_subject:
                st.error("Please select a subject folder before converting")
            else:
                # Show loading spinner during conversion
                with st.spinner('Converting file...'):
                    # Use utility function to process file
                    success, markdown_text, error_message = process_uploaded_file(
                        uploaded_file, 
                        st.session_state.converter, 
                        selected_subject
                    )
                    
                    if success:
                        # Store markdown in session state
                        st.session_state.markdown_content = markdown_text
                        st.session_state.conversion_complete = True
                        
                        # Show success message
                        st.success("✅ Conversion completed! You can now save to database.")
                        
                        # Provide download button for the converted Markdown
                        output_filename = os.path.splitext(uploaded_file.name)[0] + '.md'
                        st.download_button(
                            label="Download Markdown file",
                            data=markdown_text,
                            file_name=output_filename,
                            mime="text/markdown"
                        )
                    else:
                        # Display error message
                        st.error(error_message)
        else:
            st.warning("Please upload a file first")

    # Show save button after successful conversion
    if st.session_state.conversion_complete and st.session_state.markdown_content:
        st.markdown("---")
        st.markdown("### Save to Database")
        
        # Display selected subject
        st.info(f"📁 Subject folder: **{selected_subject}**")
        
        # Save to database button
        if st.button("💾 Save File to Database", type="primary", key='save_pdf_button'):
            if not file_title:
                st.error("Please enter a file name before saving")
            else:
                with st.spinner('Saving to database...'):
                    # Use utility function to save to database
                    success, error_message = save_to_database(
                        supabase,
                        file_title, 
                        selected_subject,
                        st.session_state.markdown_content
                    )
                    
                    if success:
                        st.success(f"✅ Document saved successfully to '{selected_subject}' folder!")
                        
                        # Reset session state after successful save
                        st.session_state.markdown_content = None
                        st.session_state.conversion_complete = False
                        
                        # Show success message
                        st.balloons()
                    else:
                        st.error(error_message)
                        st.error("Please check your Supabase credentials and table configuration.")

# Footer
st.divider()
st.caption("Built with ❤️ using Streamlit and Google Gemini | Week 9 Integration Workshop")