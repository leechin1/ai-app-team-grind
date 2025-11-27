"""
Processador principal de documentos.
"""

from typing import Optional
import mimetypes
from pathlib import Path
import os

from core.models import (
    DocumentType,
    DocumentMetadata,
    ProcessedDocument
)
from utils.text_extraction import TextExtractor
from utils.gemini_vision import GeminiVisionExtractor


class DocumentProcessor:
    """Processa documentos e extrai texto estruturado"""
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        """
        Args:
            gemini_api_key: API key do Gemini (necessária para processar imagens)
                           Se None, tenta ler de variável de ambiente GEMINI_API_KEY
        """
        self.text_extractor = TextExtractor()
        
        # Só inicializa Gemini Vision se houver API key
        if gemini_api_key is None:
            gemini_api_key = os.getenv('GEMINI_API_KEY')
        
        if gemini_api_key:
            self.vision_extractor = GeminiVisionExtractor(gemini_api_key)
        else:
            self.vision_extractor = None
    
    def process_document(
        self,
        file_bytes: bytes,
        filename: str,
        mime_type: Optional[str] = None
    ) -> ProcessedDocument:
        """Processa um documento e extrai texto"""
        
        # 1. Determina tipo
        if mime_type is None:
            mime_type, _ = mimetypes.guess_type(filename)
        
        doc_type = self._determine_document_type(mime_type, filename)
        
        # 2. Extrai texto baseado no tipo
        content, num_pages, extraction_method = self._extract_text(
            file_bytes, 
            doc_type
        )
        
        # 3. Valida
        if not content or len(content.strip()) < 10:
            raise ValueError(
                f"Texto insuficiente extraído. "
                f"Obtido: {len(content)} caracteres"
            )
        
        # 4. Cria metadados
        metadata = DocumentMetadata(
            document_type=doc_type,
            filename=filename,
            file_size_bytes=len(file_bytes),
            extracted_text_length=len(content),
            extraction_method=extraction_method,
            num_pages=num_pages
        )
        
        # 5. Preview
        preview = content[:200] + "..." if len(content) > 200 else content
        
        return ProcessedDocument(
            metadata=metadata,
            content=content,
            preview=preview
        )
    
    def process_text_input(
        self, 
        text: str, 
        source_name: str = "Text Editor"
    ) -> ProcessedDocument:
        """Processa texto direto (do text editor)"""
        
        if not text or len(text.strip()) < 10:
            raise ValueError("Texto muito curto (mínimo 10 caracteres)")
        
        content = text.strip()
        
        metadata = DocumentMetadata(
            document_type=DocumentType.TEXT,
            filename=source_name,
            file_size_bytes=len(content.encode('utf-8')),
            extracted_text_length=len(content),
            extraction_method="direct_input",
            num_pages=None
        )
        
        preview = content[:200] + "..." if len(content) > 200 else content
        
        return ProcessedDocument(
            metadata=metadata,
            content=content,
            preview=preview
        )
    
    def _extract_text(
        self, 
        file_bytes: bytes, 
        doc_type: DocumentType
    ) -> tuple[str, Optional[int], str]:
        """Extrai texto baseado no tipo"""
        
        if doc_type == DocumentType.PDF:
            content, num_pages = self.text_extractor.extract_from_pdf(file_bytes)
            return content, num_pages, "pypdf2"
        
        elif doc_type == DocumentType.DOCX:
            content = self.text_extractor.extract_from_docx(file_bytes)
            return content, None, "python-docx"
        
        elif doc_type == DocumentType.IMAGE:
            # ✅ USA GEMINI VISION em vez de Tesseract
            if self.vision_extractor is None:
                raise ValueError(
                    "Processamento de imagens requer GEMINI_API_KEY configurada. "
                    "Define a variável de ambiente ou passa api_key ao construtor."
                )
            
            content = self.vision_extractor.extract_text_from_image(file_bytes)
            return content, None, "gemini-2.5-flash-lite"
        
        elif doc_type == DocumentType.TEXT:
            content = self.text_extractor.extract_from_text(file_bytes)
            return content, None, "direct"
        
        else:
            raise ValueError(f"Tipo não suportado: {doc_type}")
    
    def _determine_document_type(
        self, 
        mime_type: Optional[str], 
        filename: str
    ) -> DocumentType:
        """Determina tipo de documento"""
        
        ext = Path(filename).suffix.lower().lstrip('.')
        
        extension_map = {
            'pdf': DocumentType.PDF,
            'docx': DocumentType.DOCX,
            'doc': DocumentType.DOCX,
            'txt': DocumentType.TEXT,
            'md': DocumentType.TEXT,
            'jpg': DocumentType.IMAGE,
            'jpeg': DocumentType.IMAGE,
            'png': DocumentType.IMAGE,
            'bmp': DocumentType.IMAGE,
            'tiff': DocumentType.IMAGE,
            'tif': DocumentType.IMAGE,
            'webp': DocumentType.IMAGE,  
        }
        
        if ext in extension_map:
            return extension_map[ext]
        
        if mime_type:
            if 'pdf' in mime_type:
                return DocumentType.PDF
            elif 'word' in mime_type or 'document' in mime_type:
                return DocumentType.DOCX
            elif 'image' in mime_type:
                return DocumentType.IMAGE
            elif 'text' in mime_type:
                return DocumentType.TEXT
        
        raise ValueError(
            f"Tipo de documento não determinado: {filename}\n"
            f"Suportados: {list(extension_map.keys())}"
        )