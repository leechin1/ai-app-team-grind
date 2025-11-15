"""
Status: Working but not cleaned
"""

import streamlit as st
from dotenv import load_dotenv
import json
import base64
from datetime import datetime
from typing import List, Dict
import os
import time

from streamlit_quill import st_quill

# Import required libraries
from docling.document_converter import DocumentConverter
import logging
from supabase_integration.fetching import *
from supabase_integration.init_push import *
from ai_comp.doc_process import * 

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

# =========================
# TAB 1: TEXT EDITOR
# =========================
with tab1:
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
        logger.info("=== TAB 1: Save button clicked ===")
        # Validate inputs
        if not file_title:
            st.error("Please enter a file name")
            logger.warning("No file title provided")
        elif not st.session_state.doc:
            st.error("Please write some content before saving")
            logger.warning("No content in editor")
        elif not selected_subject:
            st.error("Please select a subject folder")
            logger.warning("No subject selected")
        else:
            logger.info(f"Processing text editor content. Length: {len(st.session_state.doc)}")
            
            # First let's render the Gemini powered components
            summarizer = DocStorageCleaner(model="gemini-2.5-flash")
            logger.info("Summarizer initialized")

            # Run the summarization 
            try:
                logger.info("Starting summarization...")
                summary = summarizer.summariser_action(
                    st.session_state.doc,
                    pydantic_model=DocumentSummary
                )
                logger.info("Summarization complete")
                
                # Parse the JSON string back to dict
                summary_dict = json.loads(summary)
                logger.info(f"Summary parsed: {summary_dict.keys()}")

                with st.spinner('Saving to database...'):
                    # Use utility function to save to database
                    success, error_message = save_to_database(
                        supabase,
                        file_title, 
                        selected_subject,
                        st.session_state.doc,
                        short_summary=summary_dict['short_summary']['summary_text'],
                        clean_text=summary_dict['clean_text']['summary_text'],
                        key_terms=[term['term'] for term in summary_dict.get('key_terms', [])],
                        image_metadata=[]  # No images from text editor
                    )
                    
                    if success:
                        logger.info("✅ Successfully saved to database")
                        st.success(f"✅ Document saved successfully to '{selected_subject}' folder!")
                        st.balloons()
                        
                        # Optionally clear the editor after save
                        st.session_state.doc = ""
                        st.rerun()
                    else:
                        logger.error(f"Failed to save: {error_message}")
                        st.error(error_message)
                        st.error("Please check your Supabase credentials and table configuration.")
            except Exception as e:
                logger.error(f"Error during summarization or saving: {str(e)}", exc_info=True)
                st.error(f"Error processing document: {str(e)}")

# =========================
# TAB 2: PDF UPLOAD
# =========================
with tab2:
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
    if 'image_metadata' not in st.session_state:
        st.session_state.image_metadata = []

    # File upload widget
    uploaded_file = st.file_uploader(
        "Upload your PDF file",
        type=['pdf'],
        key='pdf_uploader',
        help="Drag and drop or click to select a file (max 200MB)"
    )

    # Convert button
    convert_clicked = st.button("Convert to Markdown", type="primary", key='convert_button')

    # Process conversion when button is clicked
    if convert_clicked:
        logger.info("=== TAB 2: Convert button clicked ===")
        if uploaded_file is not None:
            # Validate file name
            if not file_title:
                st.error("Please enter a file name before converting")
                logger.warning("No file title provided")
            elif not selected_subject:
                st.error("Please select a subject folder before converting")
                logger.warning("No subject selected")
            else:
                logger.info(f"Processing PDF: {uploaded_file.name}, Size: {uploaded_file.size} bytes")
                logger.info(f"Subject: {selected_subject}")
                
                # Show loading spinner during conversion
                with st.spinner('Converting file and extracting images...'):
                    try:
                        # Use utility function to process file
                        success, markdown_text, image_metadata, error_message = process_uploaded_file(
                            uploaded_file, 
                            st.session_state.converter, 
                            selected_subject,
                            supabase  
                        )
                        
                        logger.info(f"Conversion result - Success: {success}")
                        if success:
                            logger.info(f"Markdown length: {len(markdown_text) if markdown_text else 0}")
                            logger.info(f"Images extracted: {len(image_metadata)}")
                            
                            st.session_state.markdown_content = markdown_text
                            st.session_state.image_metadata = image_metadata  
                            st.session_state.conversion_complete = True
                            
                            # Show image count
                            if image_metadata:
                                st.success(f"✅ Conversion completed! Found {len(image_metadata)} images.")
                                logger.info(f"Image URLs: {[img['url'] for img in image_metadata]}")
                            else:
                                st.success("✅ Conversion completed! (No images found)")
                        else:
                            logger.error(f"Conversion failed: {error_message}")
                            st.error(error_message)
                    except Exception as e:
                        logger.error(f"Exception during conversion: {str(e)}", exc_info=True)
                        st.error(f"Error: {str(e)}")
        else:
            st.warning("Please upload a file first")
            logger.warning("Convert clicked but no file uploaded")

    # Show save button after successful conversion
    if st.session_state.conversion_complete and st.session_state.markdown_content:
        st.markdown("---")
        st.markdown("### Save to Database")
        
        # Display selected subject
        st.info(f"📁 Subject folder: **{selected_subject}**")
        
        # Show image count
        if st.session_state.image_metadata:
            st.info(f"🖼️ Images extracted: **{len(st.session_state.image_metadata)}**")
        
        # Display preview of markdown (first 500 chars)
        with st.expander("Preview Markdown Content"):
            st.text(st.session_state.markdown_content[:500] + "...")
        
        # Save to database button
        if st.button("💾 Save File to Database", type="primary", key='save_pdf_button'):
            logger.info("=" * 80)
            logger.info("=== TAB 2: Save to database button clicked ===")
            logger.info("=" * 80)
            
            if not file_title:
                st.error("Please enter a file name before saving")
                logger.warning("❌ No file title provided")
            else:
                logger.info(f"📝 Document title: {file_title}")
                logger.info(f"📁 Subject folder: {selected_subject}")
                logger.info(f"📄 Markdown content length: {len(st.session_state.markdown_content)}")
                logger.info(f"🖼️ Images to save: {len(st.session_state.image_metadata)}")
                
                try:
                    # First let's render the Gemini powered components
                    with st.spinner('🤖 Generating AI summary...'):
                        logger.info("Initializing Gemini summarizer...")
                        summarizer = DocStorageCleaner(model="gemini-2.5-flash")
                        logger.info("✅ Summarizer initialized")

                        # Run the summarization on the MARKDOWN content, not doc
                        logger.info("Starting summarization of markdown content...")
                        summary = summarizer.summariser_action(
                            st.session_state.markdown_content,
                            pydantic_model=DocumentSummary
                        )
                        logger.info("✅ Summarization complete")
                        logger.info(f"Summary length: {len(summary)} characters")
                    
                    # Parse the JSON string back to dict
                    summary_dict = json.loads(summary)
                    logger.info(f"✅ Summary parsed successfully")
                    logger.info(f"Summary keys: {summary_dict.keys()}")
                    
                    # Extract key terms list
                    key_terms_list = [
                        term['term'] for term in summary_dict.get('key_terms', [])
                    ] if summary_dict.get('key_terms') else []
                    logger.info(f"📚 Extracted {len(key_terms_list)} key terms")
                    
                    with st.spinner('💾 Saving to database...'):
                        logger.info("Calling save_to_database function...")
                        logger.info(
                            f"Parameters: title={file_title}, subject={selected_subject}, "
                            f"images={len(st.session_state.image_metadata)}"
                        )
                        
                        # Use utility function to save to database
                        success, error_message = save_to_database(
                            supabase,
                            file_title, 
                            selected_subject,
                            st.session_state.markdown_content,
                            short_summary=summary_dict['short_summary']['summary_text'],
                            clean_text=summary_dict['clean_text']['summary_text'],
                            key_terms=key_terms_list,
                            image_metadata=st.session_state.get('image_metadata', [])  
                        )
                        
                        logger.info(
                            f"save_to_database returned: success={success}, error={error_message}"
                        )
                        
                        if success:
                            logger.info("=" * 80)
                            logger.info(
                                "✅ ✅ ✅ Successfully saved to database with images ✅ ✅ ✅"
                            )
                            logger.info("=" * 80)
                            
                            st.success(
                                f"✅ Document '{file_title}' saved successfully to "
                                f"'{selected_subject}' folder!"
                            )
                            st.success(
                                f"🖼️ Saved {len(st.session_state.image_metadata)} images"
                            )
                            
                            # Show success message BEFORE clearing state
                            st.balloons()
                            
                            # Wait a moment for user to see the message
                            time.sleep(10)
                            
                            # Reset ALL PDF-related session state after successful save
                            logger.info("Clearing PDF-related session state...")
                            st.session_state.markdown_content = None
                            st.session_state.conversion_complete = False
                            st.session_state.image_metadata = []
                            # Also clear the file uploader
                            if 'pdf_uploader' in st.session_state:
                                del st.session_state['pdf_uploader']
                            
                            logger.info("Session state cleared, rerunning app...")
                            st.rerun()
                        else:
                            logger.error("=" * 80)
                            logger.error(
                                f"❌ Failed to save to database: {error_message}"
                            )
                            logger.error("=" * 80)
                            st.error(f"❌ Error: {error_message}")
                            st.error(
                                "Please check your Supabase credentials and table configuration."
                            )
                            
                except Exception as e:
                    logger.error("=" * 80)
                    logger.error(
                        f"❌ EXCEPTION during summarization or saving: {str(e)}"
                    )
                    logger.error("=" * 80)
                    logger.error("Full traceback:", exc_info=True)
                    st.error(f"❌ Error processing document: {str(e)}")
                    st.error("Check the logs for details.")

# Footer
# st.divider()
# st.caption("Built with ❤️ using Streamlit and Google Gemini | Week 9 Integration Workshop")
