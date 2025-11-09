"""
Utility functions for PDF to Markdown converter
"""
import streamlit as st
import logging
from supabase import Client
import os 
from supabase import create_client, Client 
from dotenv import load_dotenv  

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize Supabase client
@st.cache_resource
def init_supabase():
    """
    Initialize Supabase client with API credentials

    Returns: 
        Inst. client with Supabase credentials
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_API_KEY")
    if not url or not key:
        st.error("Supabase credentials not found. Please check your .env file.")
        logger.error("Missing SUPABASE_URL or SUPABASE_API_KEY in environment variables")
        st.stop()
    logger.info(f"Supabase initialized with URL: {url}")
    return create_client(url, key)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_subject_folders(_supabase: Client):
    """
    Fetch unique subject names from Supabase subject table
    
    Args:
        _supabase: Supabase client (prefixed with _ to exclude from caching)
    
    Returns:
        list: Sorted list of unique subject names
    """
    try:
        logger.info("Fetching subject folders from Supabase...")
        response = _supabase.table("subject").select("subject_name").execute()
        
        if response.data:
            # Extract unique subject names
            subject_names = [item['subject_name'] for item in response.data if item.get('subject_name')]
            # Remove duplicates and sort
            unique_subjects = sorted(list(set(subject_names)))
            logger.info(f"Fetched {len(unique_subjects)} unique subjects: {unique_subjects}")
            return unique_subjects
        else:
            logger.warning("No subjects found in database, using default list")
            return ["Mathematics", "Physics", "Chemistry", "Biology", "Computer Science", "Other"]
            
    except Exception as e:
        logger.error(f"Error fetching subjects from database: {str(e)}", exc_info=True)
        # Return default subjects if fetch fails
        return ["Mathematics", "Physics", "Chemistry", "Biology", "Computer Science", "Other"]


def process_uploaded_file(uploaded_file, converter, selected_subject):
    """
    Process uploaded PDF file and convert to Markdown
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        converter: DocumentConverter instance
        selected_subject: Selected subject folder name
    
    Returns:
        tuple: (success: bool, markdown_text: str, error_message: str)
    """
    import tempfile
    import os
    
    try:
        # Create a temporary file to store the uploaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            # Write uploaded file content to temporary file
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
            logger.debug(f"Temporary file created at: {tmp_path}")

            try:
                # Convert the PDF to Markdown using docling
                result = converter.convert(tmp_path)
                markdown_text = result.document.export_to_markdown()
                
                logger.info(f"Conversion completed. Markdown length: {len(markdown_text)} characters")
                
                return True, markdown_text, None

            except Exception as e:
                # Log and return conversion errors
                logger.error(f"Error converting file: {str(e)}")
                return False, None, f"Error converting file: {str(e)}"
            
            finally:
                # Clean up: delete temporary file regardless of success/failure
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    logger.debug("Temporary file deleted")

    except Exception as e:
        # Handle errors in file processing
        logger.error(f"Error processing file: {str(e)}")
        return False, None, f"Error processing file: {str(e)}"


def save_to_database(_supabase: Client, file_title, subject_folder: str, markdown_content: str):
    """
    Save markdown content to Supabase database
    
    Args:
        _supabase: Supabase client (prefixed with _ to exclude from caching if needed)
        file_title: Name of the file
        subject_folder: Subject folder name
        markdown_content: Markdown text content
    
    Returns:
        tuple: (success: bool, error_message: str)
    """
    try:
        logger.info(f"Attempting to save to database. File name: {file_title}")
        logger.info(f"Attempting to save to database. Subject: {subject_folder}")
        logger.info(f"Markdown content length: {len(markdown_content)}")
        
        # Prepare data for insertion
        data = {
            "title": file_title,
            "subject_folder": subject_folder,
            "markdown": markdown_content
        }
        
        logger.debug(f"Data to insert: file_title = {data["title"]}, subject_folder={data['subject_folder']}, markdown length={len(data['markdown'])}")
        
        # Insert data into Supabase regular_doc table
        response = _supabase.table("regular_doc").insert(data).execute()
        
        logger.debug(f"Supabase response: {response}")
        
        # Check if insertion was successful
        if response.data:
            logger.info(f"Document saved successfully. Response: {response.data}")
            return True, None
        else:
            logger.error(f"Database insertion failed. Full response: {response}")
            return False, "Failed to save document to database - no data returned."
            
    except Exception as e:
        logger.error(f"Error saving to database: {str(e)}", exc_info=True)
        return False, f"Error saving to database: {str(e)}"