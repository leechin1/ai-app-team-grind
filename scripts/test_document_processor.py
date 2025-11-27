"""
Testa o DocumentProcessor com diferentes tipos de ficheiros.
"""

import sys
from pathlib import Path

# Adiciona raiz do projeto ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.document_processor import DocumentProcessor


def test_text_file():
    """Testa com ficheiro de texto simples"""
    print("Teste 1: Ficheiro TXT")
    print("-" * 60)
    
    # Cria texto de teste
    test_content = """
    A mitocôndria é uma organela celular responsável pela produção de energia.
    
    Através do processo de respiração celular, a mitocôndria converte glucose
    e oxigénio em ATP (adenosina trifosfato), a molécula de energia da célula.
    
    A mitocôndria possui duas membranas: uma externa lisa e uma interna com
    cristas mitocondriais, onde ocorre a fosforilação oxidativa.
    """
    
    # Converte para bytes (simula upload de ficheiro)
    file_bytes = test_content.encode('utf-8')
    
    # Processa
    processor = DocumentProcessor()

    try:
        result = processor.process_document(
            file_bytes=file_bytes,
            filename="teste.txt"
        )

        print(f"Tipo: {result.metadata.document_type}")
        print(f"Metodo: {result.metadata.extraction_method}")
        print(f"Tamanho: {result.metadata.extracted_text_length} chars")
        print(f"\nPreview:")
        print(result.preview)
        print("\n[OK] Teste 1 passou!\n")
        return True

    except Exception as e:
        print(f"[FALHOU] Teste 1 falhou: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_direct_text():
    """Testa com texto direto (editor)"""
    print("Teste 2: Texto Direto")
    print("-" * 60)

    text = "Isto e um teste de entrada de texto direto do editor."

    processor = DocumentProcessor()

    try:
        result = processor.process_text_input(text, "Editor de Texto")

        print(f"Tipo: {result.metadata.document_type}")
        print(f"Metodo: {result.metadata.extraction_method}")
        print(f"Conteudo: {result.content}")
        print("\n[OK] Teste 2 passou!\n")
        return True

    except Exception as e:
        print(f"[FALHOU] Teste 2 falhou: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("TESTES DO DOCUMENT PROCESSOR")
    print("=" * 60)
    print()

    results = []

    # Roda testes
    results.append(test_text_file())
    results.append(test_direct_text())

    # Resumo
    print("=" * 60)
    print("RESUMO")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Testes passados: {passed}/{total}")

    if passed == total:
        print("\n[OK] Todos os testes passaram!")
    else:
        print(f"\n[FALHOU] {total - passed} teste(s) falharam")
        sys.exit(1)