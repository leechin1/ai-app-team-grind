"""
Simple test for document processor with text file.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.document_processor import DocumentProcessor

print("Testing DocumentProcessor with text content...")

# Test content
test_content = """
A mitocondria e uma organela celular responsavel pela producao de energia.

Atraves do processo de respiracao celular, a mitocondria converte glucose
e oxigenio em ATP (adenosina trifosfato), a molecula de energia da celula.
"""

# Convert to bytes (simulate file upload)
file_bytes = test_content.encode('utf-8')

# Process
processor = DocumentProcessor()

try:
    result = processor.process_document(
        file_bytes=file_bytes,
        filename="test.txt"
    )

    print("SUCCESS: Document processed!")
    print(f"  - Document type: {result.metadata.document_type}")
    print(f"  - Extraction method: {result.metadata.extraction_method}")
    print(f"  - Text length: {result.metadata.extracted_text_length} chars")
    print(f"\nPreview:")
    print("-" * 60)
    print(result.preview)
    print("-" * 60)

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\nTest completed!")
