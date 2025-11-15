# fetching.py
import streamlit as st
import logging
from supabase import Client, create_client
import os 
from dotenv import load_dotenv
from typing import List, Dict, Optional
from datetime import datetime, timedelta

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


@st.cache_data(ttl=60)  # Cache for 60 seconds
def get_subject_folders(_supabase_client: Client) -> List[str]:
    """
    Fetch all subject folders from subject table
    Uses cache with 60s TTL to reduce database calls
    
    Note: _supabase_client has underscore prefix to exclude from cache key
    """
    try:
        logger.info("Fetching subjects from database...")
        response = _supabase_client.table("subject")\
            .select("subject_name")\
            .order("subject_name")\
            .execute()
        
        subjects = [subject['subject_name'] for subject in response.data]
        logger.info(f"Found {len(subjects)} subjects")
        return subjects
    except Exception as e:
        logger.error(f"Error fetching subjects: {e}", exc_info=True)
        return []


@st.cache_data(ttl=30)  # Cache for 30 seconds - documents change more frequently
def fetch_documents_by_subject(_supabase_client: Client, subject_folder: str) -> List[Dict]:
    """
    Fetch all documents for a specific subject with caching
    
    Args:
        _supabase_client: Supabase client (excluded from cache key with _)
        subject_folder: Name of the subject folder
    
    Returns:
        List of document dictionaries with metadata
    """
    try:
        logger.info(f"Fetching documents for subject: {subject_folder}")
        response = _supabase_client.table("regular_doc")\
            .select("id, title, created_at, key_terms, short_summary, images")\
            .eq("subject_folder", subject_folder)\
            .order("created_at", desc=True)\
            .execute()
        
        logger.info(f"Found {len(response.data)} documents for '{subject_folder}'")
        logger.debug(f"Documents: {response.data}")
        return response.data
    except Exception as e:
        logger.error(f"Error fetching documents for '{subject_folder}': {e}", exc_info=True)
        return []


@st.cache_data(ttl=300)  # Cache full document for 5 minutes
def fetch_document_details(_supabase_client: Client, doc_id: int) -> Optional[Dict]:
    """
    Fetch complete document details including full content
    Cached longer since document content rarely changes
    
    Args:
        _supabase_client: Supabase client
        doc_id: Document ID
    
    Returns:
        Complete document dictionary or None
    """
    try:
        logger.info(f"Fetching document details for ID: {doc_id}")
        response = _supabase_client.table("regular_doc")\
            .select("*")\
            .eq("id", doc_id)\
            .single()\
            .execute()
        
        logger.info(f"Successfully fetched document: {response.data.get('title', 'Unknown')}")
        return response.data
    except Exception as e:
        logger.error(f"Error fetching document {doc_id}: {e}", exc_info=True)
        return None


def create_new_subject(_supabase_client: Client, subject_name: str) -> tuple[bool, str]:
    """
    Create a new subject in the database
    Note: Not cached since we want immediate updates
    
    Args:
        _supabase_client: Supabase client
        subject_name: Name of the new subject
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        logger.info(f"Creating new subject: {subject_name}")
        response = _supabase_client.table("subject")\
            .insert({"subject_name": subject_name})\
            .execute()
        
        if response.data:
            logger.info(f"Subject created successfully: {subject_name}")
            
            # Clear the subjects cache to show new subject immediately
            st.cache_data.clear()
            
            return True, "Subject created successfully!"
        else:
            logger.error(f"Failed to create subject: no data returned")
            return False, "Failed to create subject"
    except Exception as e:
        logger.error(f"Error creating subject: {e}", exc_info=True)
        return False, f"Error: {str(e)}"


# Manual cache clearing functions
def clear_subjects_cache():
    """Clear only subjects cache"""
    get_subject_folders.clear()
    logger.info("Subjects cache cleared")


def clear_documents_cache():
    """Clear documents cache for all subjects"""
    fetch_documents_by_subject.clear()
    logger.info("Documents cache cleared")


def clear_all_caches():
    """Clear all Streamlit caches"""
    st.cache_data.clear()
    logger.info("All caches cleared")


def debug_cache_info():
    """Display cache information in sidebar (for debugging)"""
    with st.sidebar.expander("🔍 Cache Debug Info"):
        st.write("Cache Status:")
        st.write(f"- Subjects cached: {'subjects_cache' in st.session_state}")
        st.write(f"- Current session keys: {list(st.session_state.keys())}")
        
        if st.button("🗑️ Clear All Caches"):
            clear_all_caches()
            st.success("Caches cleared!")
            st.rerun()