# doc_process.py
"""
The following script contemplates the initial steps when saving the doc to supabase.
This file is meant to operate with supabase_integration/ init_push.py
"""

from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Type, Dict
import json
import docling
import uuid
import logging
from supabase import Client


load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
logger = logging.getLogger(__name__)

# Pydantic classes

class ShortSummary(BaseModel):
    """A concise, text-based summary limited to only what is written in the document."""
    summary_text: str = Field(..., description="Condensed version of the document’s main points (≤ 3 sentences).")

class CleanText(BaseModel):
    """A cleaner version of the text."""
    summary_text: str = Field(..., description="The text with: fixed grammatical errors and typos; organised structured information; formatted text blocks")

class KeyTerms(BaseModel):
    """Lists key terms and their definitions exactly as given in the document."""
    term: str = Field(..., description="Key term as written in the document.")
    definition: str = Field(..., description="Definition of the terms as explicitly stated in the document.")


# Aggregating everything together
class DocumentSummary(BaseModel):
    """Aggregates all textual summaries and metadata for one document."""
    short_summary: ShortSummary
    clean_text: CleanText
    key_terms: Optional[List[KeyTerms]] = None


# System Prompt
SYSTEM_PROMPT = """You are an expert note processing assistant that performs two critical tasks:

## Task 1: Clean and Format Raw Notes
Take messy, incomplete raw notes and transform them into well-structured, readable markdown while being 100% faithful to the original content. Your formatting responsibilities:

### Formatting Rules:
1. **Fix grammatical errors and typos** - correct spelling, grammar, and sentence structure
2. **Organize content hierarchically** - use proper heading levels (H1, H2, H3, etc.)
3. **Structure information logically** - group related concepts together
4. **Format code blocks properly** - use syntax highlighting for code
5. **Create clear lists** - convert unstructured points into bulleted or numbered lists
6. **Add visual hierarchy** - use bold, italic, and other markdown features appropriately
7. **Preserve all technical terms and definitions** - never change technical vocabulary
8. **Maintain all original information** - do not add external knowledge or examples
9. **Clean up formatting artifacts** - remove stray symbols, fix spacing issues

### Structural Guidelines:
- Main topics → H1 (#)
- Subtopics → H2 (##)
- Specific concepts → H3 (###)
- Details → H4 (####)
- Use code blocks with language specification for code
- Use tables for structured comparisons when appropriate
- Use callouts or blockquotes for important notes or warnings

## Task 2: Extract Structured Metadata
After cleaning the text, extract structured information following these strict rules:

### Extraction Rules:
1. **Stay 100% faithful to the source text** - never invent or infer information
2. **Use exact phrases** - copy terms and definitions verbatim when possible
3. **Only include explicitly stated information** - if something isn't mentioned, leave it as None/null
4. **For key terms** - only extract terms that have clear definitions in the text
5. **For references** - only extract if actual citations or sources are mentioned
6. **For further research** - only include if the document explicitly suggests areas for exploration
7. **For topics** - identify what the document explicitly states it's about, not what you think it's about

### What NOT to do:
- Don't add information not present in the source
- Don't make assumptions about implicit meanings
- Don't include general knowledge about the topic
- Don't create definitions for terms not defined in the text
- Don't infer research directions not explicitly mentioned
- Don't standardize or normalize technical content


Be thorough but stay faithful to the source material."""



class DocStorageCleaner:
    """
    Extracts structured, strictly text-grounded summaries from Markdown documents
    into a Pydantic schema (e.g., DocumentSummary).
    No inference, guessing, or external knowledge is permitted.
    """

    def __init__(self, model: str = "gemini-2.0-flash"):
        self.model_name = model
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.system_instruction = SYSTEM_PROMPT

    def _build_prompt(self, markdown_doc: str) -> str:
        """Builds the extraction prompt used for the summarization agent."""
        return f"""
You are an educational summarization agent.
Your task is to extract information ONLY from the given Markdown document, with zero interpretation, speculation, or external knowledge.

Follow these strict rules:
1. Use only what is explicitly written.
2. Do NOT infer or fabricate.
3. Maintain textual fidelity—copy or minimally paraphrase phrases.
4. If a field is absent, output null.
5. Output must be valid JSON conforming to the provided Pydantic schema.

## HOW TO FILL THE PYDANTIC MODELS:

### For `clean_text` (CleanText model):
**What to look for:**
- Scan the entire document from top to bottom
- Identify all content blocks: headers, paragraphs, lists, code, formulas
- Note grammatical errors, typos, inconsistent formatting, broken lists, missing punctuation
- Look for redundant phrases, run-on sentences, unclear structure
- Identify technical terms, definitions, examples, code snippets that must be preserved

**How to process:**
- Rewrite each sentence with correct grammar while keeping the same meaning
- Fix spelling errors and typos
- Convert fragmented notes into complete sentences where appropriate
- Organize scattered information into logical sections with proper headers
- Format code blocks with proper syntax (```language)
- Make bullet points consistent and properly formatted
- Remove duplicate information
- Ensure proper spacing and line breaks
- **CRITICAL**: Every piece of information from the original must appear in clean_text
- **Output**: Single long string of markdown-formatted text with ALL original content

### For `short_summary` (ShortSummary model):
**What to look for:**
- Main topic or title of the document (usually in headers)
- Core concepts being explained (look for definitions, explanations)
- Primary purpose or learning objective (what is this teaching?)
- Key takeaways or conclusions (often at end or in summary sections)
- Main categories or sections covered

**How to process:**
- Write 2-3 sentences maximum (≤ 3 sentences is strict requirement)
- First sentence: State the main topic/subject of the document
- Second sentence: Mention 2-4 most important concepts or points covered
- Third sentence (optional): State the purpose or application if explicitly mentioned
- Use only information directly stated in the document
- Do NOT add context, background, or explanations not in the source
- **Output**: Concise text (2-3 sentences) that captures essence without detail

### For `key_terms` (List of KeyTerms models):
**What to look for:**
- Explicit definitions in the format: "Term: definition" or "Term - definition" or "**Term**: definition"
- Sections labeled "Key Terms", "Definitions", "Glossary", "Terminology"
- Bold or emphasized words followed by explanations
- Sentences structured as "X is defined as..." or "X refers to..." or "X means..."
- Technical vocabulary that appears with immediate explanation
- Concepts introduced with "In other words", "i.e.", "that is"

DOCUMENT:
---
{markdown_doc}
---
        """.strip()

    def summariser_action(
        self,
        markdown_doc: str,
        pydantic_model: Type[BaseModel],
    ) -> BaseModel:
        """
        Summarizes a Markdown document into the provided Pydantic model.

        Args:
            markdown_doc: Raw Markdown text to analyze.
            pydantic_model: The target Pydantic BaseModel (e.g., DocumentSummary).

        Returns:
            Parsed Pydantic model with extracted content.
        """
        prompt = self._build_prompt(markdown_doc)

        config = types.GenerateContentConfig(
            system_instruction=self.system_instruction,
            response_mime_type="application/json",
            response_schema=pydantic_model,
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config,
        )

        # Parse the JSON response into the Pydantic model
        result = pydantic_model.model_validate_json(response.text)
        print("Extraction successful!")
        return result.model_dump_json(indent=2)
    
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
