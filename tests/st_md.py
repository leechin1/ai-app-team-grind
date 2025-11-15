# Prototyping the Markdown file conversion. Component embedded in tab 2 of text_input

# Import required libraries
import streamlit as st  # Web app framework
from docling.document_converter import DocumentConverter  # PDF conversion library
import os  # For file operations
import logging  # For debugging and error tracking
from dotenv import load_dotenv  # Load environment variables
from utils.supabase_utils import init_supabase, get_subject_folders, process_uploaded_file, save_to_database  # Import utility functions

# Load environment variables from .env file
load_dotenv()

# Configure logging to help with debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Supabase client using utility function
supabase = init_supabase()

# Custom CSS for better layout
st.markdown("""
    <style>    
        .stFileUploader {
            padding: 1rem;
        }
        
        button[data-testid="stFileUploaderButtonPrimary"] {
            background-color: #000660 !important;
            border: none !important;
            color: white !important;
        }

        .stButton button {
            background-color: #006666;
            border: none !important;
            color: white;
            padding: 0.5rem 2rem !important;
        }
        .stButton button:hover {
            background-color: #008080 !important;
            color: white !important;
            border-color: #008080 !important;
        }
        .upload-text {
            font-size: 1.2rem;
            margin-bottom: 1rem;
        }
        div[data-testid="stFileUploadDropzone"]:hover {
            border-color: #006666 !important;
            background-color: rgba(0, 102, 102, 0.05) !important;
        }
    </style>
""", unsafe_allow_html=True)

# Display the app title
st.title("PDF to Markdown Converter")


# Initialize the DocumentConverter once per session
# This prevents recreating the converter on every page reload
if 'converter' not in st.session_state:
    try:
        st.session_state.converter = DocumentConverter() # Docling vision model
        logger.debug("Converter successfully created")
    except Exception as e:
        logger.error(f"Error creating converter: {str(e)}")
        st.error(f"Error creating converter: {str(e)}")
        st.stop()  # Stop execution if converter fails to initialize

# Initialize session state for markdown content and conversion status
if "file_title" not in st.session_state:
    st.session_state.file_title = None
if 'markdown_content' not in st.session_state:
    st.session_state.markdown_content = None
if 'conversion_complete' not in st.session_state:
    st.session_state.conversion_complete = False

# Get subject folders from database using utility function
SUBJECT_FOLDERS = get_subject_folders(supabase)

# File upload widget - accepts PDF files only 
uploaded_file = st.file_uploader(
    "Upload your PDF file",
    type=['pdf'],
    key='pdf_uploader',
    help="Drag and drop or click to select a file (max 200MB)"
)

# Step 1: Select title and subject BEFORE conversion

# Asking for doc title
file_title = st.text_input("File Name")

st.markdown("### Select Subject Folder")
selected_subject = st.selectbox(
    "Choose the subject folder for this document:",
    options=SUBJECT_FOLDERS,
    key='subject_selector'
)

# Convert button
convert_clicked = st.button("Convert to Markdown", type="primary")

# Process conversion when button is clicked
if convert_clicked:
    # Handle file upload conversion
    if uploaded_file is not None:
        # Show loading spinner during conversion
        with st.spinner('Converting file...'):
            # Use utility function to process file
            success, markdown_text, error_message = process_uploaded_file(
                uploaded_file, 
                st.session_state.converter, 
                selected_subject
            )
            
            if success:
                # Store title and markdown in session state ONLY IF PARSING IS SUCCESSFUL
                st.session_state.file_title = file_title, 
                st.session_state.markdown_content = markdown_text
                st.session_state.selected_subject = selected_subject
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

# Step 3: Show save button after successful conversion
if st.session_state.conversion_complete and st.session_state.markdown_content:
    st.markdown("---")
    st.markdown("### Save to Database")
    
    # Display selected subject
    st.info(f"📁 Subject folder: **{st.session_state.selected_subject}**")
    
    # Save to database button
    if st.button("💾 Save File to Database", type="primary", key='save_button'):
        with st.spinner('Saving to database...'):
            # Use utility function to save to database
            success, error_message = save_to_database(
                supabase,
                st.session_state.file_title, 
                st.session_state.selected_subject,
                st.session_state.markdown_content
            )
            
            if success:
                st.success(f"✅ Document saved successfully to '{st.session_state.selected_subject}' folder!")
                
                # Reset session state after successful save
                st.session_state.file_title = None
                st.session_state.markdown_content = None
                st.session_state.conversion_complete = False
                st.session_state.selected_subject = None
                
                # Show success message and prompt to refresh
                st.balloons()
            else:
                st.error(error_message)
                st.error("Please check your Supabase credentials and table configuration.")