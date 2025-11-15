"""
This script handles the push of the files to the database "regular_doc"
"""
import streamlit as st
import logging
from supabase import Client
import os 
from supabase import create_client, Client 
from typing import List, Dict, Tuple
import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO
import uuid

logger = logging.getLogger(__name__)

def extract_images_from_pdf(uploaded_file, _supabase: Client, document_id: str, subject_folder: str) -> List[Dict]:
    """
    Extract images from PDF and upload to Supabase Storage.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        _supabase: Supabase client
        document_id: Unique identifier for this document
        subject_folder: Subject folder name for organizing images
    
    Returns:
        List[Dict]: List of image metadata dictionaries
    """
    image_metadata = []
    
    try:
        # Reset file pointer and open with PyMuPDF
        uploaded_file.seek(0)
        pdf_bytes = uploaded_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        logger.info(f"Extracting images from PDF with {len(doc)} pages")
        
        for page_number, page in enumerate(doc, start=1):
            images = page.get_images()
            logger.debug(f"Found {len(images)} images on page {page_number}")
            
            for img_index, img in enumerate(images, start=1):
                try:
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    # Load image to check dimensions
                    image = Image.open(BytesIO(image_bytes))
                    
                    # Skip tiny images (likely logos/icons)
                    if image.size[0] < 100 or image.size[1] < 100:
                        logger.debug(f"Skipping small image on page {page_number}: {image.size}")
                        continue
                    
                    # Create unique filename
                    filename = f"{document_id}_p{page_number}_img{img_index}.{image_ext}"
                    storage_path = f"{subject_folder}/{filename}"
                    
                    logger.debug(f"Uploading image: {storage_path} ({image.size})")
                    
                    # Upload to Supabase Storage bucket
                    _supabase.storage.from_("lecture-images").upload(
                        storage_path,
                        image_bytes,
                        file_options={"content-type": f"image/{image_ext}"}
                    )
                    
                    # Get public URL
                    image_url = _supabase.storage.from_("lecture-images").get_public_url(storage_path)
                    
                    image_metadata.append({
                        "page_number": page_number,
                        "image_index": img_index,
                        "storage_path": storage_path,
                        "url": image_url,
                        "format": image_ext,
                        "width": image.size[0],
                        "height": image.size[1]
                    })
                    
                    logger.info(f"Successfully uploaded image: {storage_path}")
                    
                except Exception as e:
                    logger.error(f"Error processing image on page {page_number}, index {img_index}: {str(e)}")
                    continue
        
        doc.close()
        logger.info(f"Extracted {len(image_metadata)} images from PDF")
        
    except Exception as e:
        logger.error(f"Error extracting images from PDF: {str(e)}")
    
    return image_metadata


def process_uploaded_file(uploaded_file, converter, selected_subject, _supabase: Client):
    """
    Process uploaded PDF file and convert to Markdown, also extract images
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        converter: DocumentConverter instance
        selected_subject: Selected subject folder name
        _supabase: Supabase client for image storage
    
    Returns:
        tuple: (success: bool, markdown_text: str, image_metadata: List[Dict], error_message: str)
    """
    import tempfile
    import os
    
    try:
        # Generate unique document ID
        document_id = str(uuid.uuid4())[:8]
        logger.info(f"Processing document with ID: {document_id}")
        
        # Extract images first (before we consume the file for markdown conversion)
        image_metadata = extract_images_from_pdf(uploaded_file, _supabase, document_id, selected_subject)
        
        # Create a temporary file to store the uploaded PDF for markdown conversion
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            # Reset file pointer and write uploaded file content to temporary file
            uploaded_file.seek(0)
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
            logger.debug(f"Temporary file created at: {tmp_path}")

            try:
                # Convert the PDF to Markdown using docling
                result = converter.convert(tmp_path)
                markdown_text = result.document.export_to_markdown()
                
                logger.info(f"Conversion completed. Markdown length: {len(markdown_text)} characters")
                logger.info(f"Extracted {len(image_metadata)} images")
                
                return True, markdown_text, image_metadata, None

            except Exception as e:
                # Log and return conversion errors
                logger.error(f"Error converting file: {str(e)}")
                return False, None, image_metadata, f"Error converting file: {str(e)}"
            
            finally:
                # Clean up: delete temporary file regardless of success/failure
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    logger.debug("Temporary file deleted")

    except Exception as e:
        # Handle errors in file processing
        logger.error(f"Error processing file: {str(e)}")
        return False, None, [], f"Error processing file: {str(e)}"


def save_to_database(_supabase: Client, 
                     file_title: str, 
                     subject_folder: str, 
                     markdown_content: str,
                     short_summary: str,
                     clean_text: str,
                     key_terms: List[str],
                     image_metadata: List[Dict] = None
                     ) -> Tuple[bool, str]:
    """
    GEMINI POWERED components rendered before storing to db. Assuming that data is already rendered
    Save markdown content and image metadata to Supabase database
    
    Args:
        _supabase: Supabase client (prefixed with _ to exclude from caching if needed)
        file_title: Name of the file
        subject_folder: Subject folder name
        markdown_content: Markdown text content
        short_summary: Short summary of doc (GEMINI POWERED)
        clean_text: More concise information (GEMINI POWERED)
        key_terms: Key terms (GEMINI POWERED)
        image_metadata: List of image metadata dictionaries (optional)
    
    Returns:
        tuple: (success: bool, error_message: str)
    """
    try:
        logger.info("=" * 80)
        logger.info("📥 SAVE_TO_DATABASE FUNCTION CALLED")
        logger.info("=" * 80)
        logger.info(f"📝 File name: {file_title}")
        logger.info(f"📁 Subject: {subject_folder}")
        logger.info(f"📄 Raw markdown content length: {len(markdown_content)}")
        logger.info(f"📝 Short summary length: {len(short_summary) if short_summary else 0}")
        logger.info(f"🧹 Clean text length: {len(clean_text) if clean_text else 0}")
        logger.info(f"📚 Key terms type: {type(key_terms)}, value: {key_terms}")
        logger.info(f"🖼️ Number of images: {len(image_metadata) if image_metadata else 0}")
        
        # Prepare data for insertion
        data = {
            "title": file_title,
            "subject_folder": subject_folder,
            "markdown": markdown_content,
            "short_summary": short_summary,
            "clean_text": clean_text,
            "key_terms": key_terms,
            "images": image_metadata if image_metadata else []  # Store as JSONB array
        }
        
        logger.info("📦 Data prepared for insertion:")
        logger.info(f"  - title: {data['title']}")
        logger.info(f"  - subject_folder: {data['subject_folder']}")
        logger.info(f"  - markdown length: {len(data['markdown'])}")
        logger.info(f"  - short_summary length: {len(data['short_summary'])}")
        logger.info(f"  - clean_text length: {len(data['clean_text'])}")
        logger.info(f"  - key_terms: {data['key_terms']}")
        logger.info(f"  - images count: {len(data['images'])}")
        
        logger.info("🚀 Inserting data into Supabase table 'regular_doc'...")
        
        # Insert data into Supabase regular_doc table
        response = _supabase.table("regular_doc").insert(data).execute()
        
        logger.info("📨 Supabase response received")
        logger.info(f"  - response.data: {response.data}")
        logger.info(f"  - response type: {type(response)}")
        
        # Check if insertion was successful
        if response.data:
            logger.info("=" * 80)
            logger.info("✅ ✅ ✅ DOCUMENT SAVED SUCCESSFULLY ✅ ✅ ✅")
            logger.info("=" * 80)
            logger.info(f"Response data: {response.data}")
            return True, None
        else:
            logger.error("=" * 80)
            logger.error("❌ DATABASE INSERTION FAILED - NO DATA RETURNED")
            logger.error("=" * 80)
            logger.error(f"Full response: {response}")
            return False, "Failed to save document to database - no data returned."
            
    except Exception as e:
        logger.error("=" * 80)
        logger.error("❌ EXCEPTION IN SAVE_TO_DATABASE")
        logger.error("=" * 80)
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error("Full traceback:", exc_info=True)
        return False, f"Error saving to database: {str(e)}"