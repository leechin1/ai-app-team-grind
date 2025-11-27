"""
Testa processamento de imagens com Gemini Vision.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.document_processor import DocumentProcessor
from dotenv import load_dotenv
import os

load_dotenv()

def test_image_processing():
    """Testa extração de texto de imagem"""
    print("🧪 Testando Gemini Vision para imagens")
    
    # Procura imagens na pasta
    image_files = list(Path.cwd().glob("*.jpg")) + \
                  list(Path.cwd().glob("*.png")) + \
                  list(Path.cwd().glob("*.jpeg"))
    
    if not image_files:
        print("⏭️  Sem imagens para testar")
        print("💡 Coloca uma imagem (.jpg/.png) na pasta raiz")
        return
    
    img_path = image_files[0]
    print(f"   Processando: {img_path.name}")
    
    # Lê imagem
    with open(img_path, 'rb') as f:
        img_bytes = f.read()
    
    # Processa
    api_key = os.getenv('GEMINI_API_KEY')
    processor = DocumentProcessor(gemini_api_key=api_key)
    
    try:
        result = processor.process_document(
            file_bytes=img_bytes,
            filename=img_path.name
        )
        
        print(f"✅ Imagem processada!")
        print(f"   Método: {result.metadata.extraction_method}")
        print(f"   Texto extraído: {result.metadata.extracted_text_length} chars")
        print(f"\n📄 Texto extraído:")
        print("="*60)
        print(result.content)
        print("="*60)
        
        # Guarda resultado
        output_path = f"extracted_{img_path.stem}.txt"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result.content)
        print(f"\n💾 Guardado em: {output_path}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_image_processing()