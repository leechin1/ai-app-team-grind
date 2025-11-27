# utils/text_extraction.py

"""
Utilitários de OCR para extrair texto de diferentes formatos.
"""

from typing import Tuple
import io

class TextExtractor:
    """Extrai texto de documentos"""
    
    @staticmethod
    def extract_from_text(file_bytes: bytes, encoding: str = 'utf-8') -> str:
        """Extrai texto de ficheiro TXT"""
        try:
            text = file_bytes.decode(encoding)
            return text.strip()
        except UnicodeDecodeError:
            try:
                text = file_bytes.decode('latin-1')
                return text.strip()
            except:
                raise ValueError(f"Não foi possível decodificar com encoding {encoding}")
    
    @staticmethod
    def extract_from_pdf(file_bytes: bytes) -> Tuple[str, int]:
        """Extrai texto de PDF. Retorna (texto, num_páginas)"""
        import PyPDF2
        
        pdf_file = io.BytesIO(file_bytes)
        
        try:
            reader = PyPDF2.PdfReader(pdf_file)
            num_pages = len(reader.pages)
            
            if num_pages == 0:
                raise ValueError("PDF vazio")
            
            text_parts = []
            for page_num in range(num_pages):
                page = reader.pages[page_num]
                text = page.extract_text()
                
                if text and text.strip():
                    text_parts.append(f"--- Página {page_num + 1} ---\n{text}")
            
            if not text_parts:
                raise ValueError("PDF não contém texto extraível")
            
            return "\n\n".join(text_parts), num_pages
            
        except PyPDF2.errors.PdfReadError as e:
            raise ValueError(f"Erro ao ler PDF: {str(e)}")
        finally:
            pdf_file.close()
    
    @staticmethod
    def extract_from_docx(file_bytes: bytes) -> str:
        """Extrai texto de DOCX"""
        import docx
        
        doc_file = io.BytesIO(file_bytes)
        
        try:
            doc = docx.Document(doc_file)
            
            paragraphs = []
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    paragraphs.append(text)
            
            if not paragraphs:
                raise ValueError("DOCX vazio")
            
            return "\n\n".join(paragraphs)
            
        except Exception as e:
            raise ValueError(f"Erro ao processar DOCX: {str(e)}")
        finally:
            doc_file.close()
    