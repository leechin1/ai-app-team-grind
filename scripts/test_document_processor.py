# -*- coding: utf-8 -*-
"""
Testa o DocumentProcessor com diferentes tipos de ficheiros.
Consolida todos os testes: texto, PDF e imagens.
"""

import sys
from pathlib import Path

# Adiciona raiz do projeto ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.document_processor import DocumentProcessor
from dotenv import load_dotenv
import os

load_dotenv()


def test_text_file():
    """Teste 1: Ficheiro de texto simples"""
    print("Teste 1: Ficheiro TXT")
    print("-" * 60)

    # Cria texto de teste
    test_content = """
    A mitocondria e uma organela celular responsavel pela producao de energia.

    Atraves do processo de respiracao celular, a mitocondria converte glucose
    e oxigenio em ATP (adenosina trifosfato), a molecula de energia da celula.

    A mitocondria possui duas membranas: uma externa lisa e uma interna com
    cristas mitocondriais, onde ocorre a fosforilacao oxidativa.
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
    """Teste 2: Texto direto (editor)"""
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


def test_pdf_extraction():
    """Teste 3: Extracao de PDF"""
    print("Teste 3: Extracao de PDF")
    print("-" * 60)

    # Procura PDFs na raiz do projeto
    root_dir = Path(__file__).parent.parent
    pdf_files = list(root_dir.glob("*.pdf"))

    if not pdf_files:
        print("[AVISO] Nenhum PDF encontrado na raiz do projeto")
        print("Coloca um ficheiro PDF na raiz para testar")
        print("[SKIP] Teste 3 pulado\n")
        return None  # None = teste pulado

    # Usa o primeiro PDF encontrado
    pdf_path = pdf_files[0]
    print(f"PDF encontrado: {pdf_path.name}")
    print(f"Tamanho: {pdf_path.stat().st_size / 1024:.2f} KB")

    # Le o PDF
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()

    # Processa
    processor = DocumentProcessor()

    try:
        result = processor.process_document(
            file_bytes=pdf_bytes,
            filename=pdf_path.name
        )

        print(f"Tipo: {result.metadata.document_type}")
        print(f"Metodo: {result.metadata.extraction_method}")
        print(f"Paginas: {result.metadata.num_pages}")
        print(f"Tamanho do texto: {result.metadata.extracted_text_length} chars")
        print(f"\nPreview do texto extraido:")
        print("=" * 60)
        print(result.preview)
        print("=" * 60)

        # Mostra estatisticas
        lines = result.content.count('\n')
        words = len(result.content.split())
        print(f"\nEstatisticas:")
        print(f"  - Linhas: {lines}")
        print(f"  - Palavras: {words}")
        print(f"  - Caracteres: {result.metadata.extracted_text_length}")

        print("\n[OK] Teste 3 passou!\n")
        return True

    except Exception as e:
        print(f"[FALHOU] Teste 3 falhou: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_image_processing():
    """Teste 4: Processamento de imagens com Gemini Vision"""
    print("Teste 4: Extracao de Imagem (Gemini Vision)")
    print("-" * 60)

    # Procura imagens na raiz do projeto
    root_dir = Path(__file__).parent.parent
    image_files = list(root_dir.glob("*.jpg")) + \
                  list(root_dir.glob("*.png")) + \
                  list(root_dir.glob("*.jpeg"))

    if not image_files:
        print("[AVISO] Nenhuma imagem encontrada na raiz do projeto")
        print("Coloca uma imagem (.jpg/.png) na raiz para testar")
        print("[SKIP] Teste 4 pulado\n")
        return None  # None = teste pulado

    # Verifica se tem API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("[AVISO] GEMINI_API_KEY nao encontrada no .env")
        print("Define a variavel de ambiente para testar imagens")
        print("[SKIP] Teste 4 pulado\n")
        return None  # None = teste pulado

    print(f"Encontradas {len(image_files)} imagem(ns) para testar\n")

    # Processa cada imagem
    processor = DocumentProcessor(gemini_api_key=api_key)
    results = []

    for i, img_path in enumerate(image_files, 1):
        print(f"  Imagem {i}/{len(image_files)}: {img_path.name}")
        print(f"  Tamanho: {img_path.stat().st_size / 1024:.2f} KB")

        try:
            # Le imagem
            with open(img_path, 'rb') as f:
                img_bytes = f.read()

            # Processa
            result = processor.process_document(
                file_bytes=img_bytes,
                filename=img_path.name
            )

            print(f"  Tipo: {result.metadata.document_type}")
            print(f"  Metodo: {result.metadata.extraction_method}")
            print(f"  Texto extraido: {result.metadata.extracted_text_length} chars")

            # Preview seguro (remove caracteres que Windows console nao suporta)
            try:
                preview = result.preview[:100]
                print(f"  Preview: {preview}...")
            except UnicodeEncodeError:
                # Fallback: mostra sem preview se tiver caracteres especiais
                print(f"  Preview: [contem caracteres especiais - ver ficheiro extraido]")

            print(f"  [OK] Imagem {i} processada com sucesso!\n")

            results.append((img_path.name, True, None))

        except Exception as e:
            print(f"  [FALHOU] Erro ao processar imagem {i}: {e}")
            print(f"  Detalhes do erro:")
            import traceback
            traceback.print_exc()
            print()

            results.append((img_path.name, False, str(e)))

    # Resumo do teste de imagens
    print("-" * 60)
    print("Resumo do Teste 4:")
    passed = sum(1 for _, success, _ in results if success)
    failed = sum(1 for _, success, _ in results if not success)
    print(f"  Passaram: {passed}/{len(results)}")
    print(f"  Falharam: {failed}/{len(results)}")

    if failed > 0:
        print("\nImagens que falharam:")
        for name, success, error in results:
            if not success:
                print(f"  - {name}: {error}")

    # Considera sucesso se pelo menos 80% das imagens passarem
    success_rate = passed / len(results) if len(results) > 0 else 0
    if success_rate >= 0.8:  # 80% ou mais
        print(f"\n[OK] Teste 4 passou! ({passed}/{len(results)} imagens processadas com sucesso)\n")
        return True
    else:
        print(f"\n[FALHOU] Teste 4 falhou (apenas {passed}/{len(results)} passaram, minimo necessario: 80%)\n")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("TESTES DO DOCUMENT PROCESSOR")
    print("=" * 60)
    print()

    results = []

    # Roda todos os testes
    results.append(test_text_file())
    results.append(test_direct_text())
    results.append(test_pdf_extraction())
    results.append(test_image_processing())

    # Resumo
    print("=" * 60)
    print("RESUMO")
    print("=" * 60)

    # Conta resultados (None = pulado, nao conta)
    executed = [r for r in results if r is not None]
    passed = sum(1 for r in executed if r is True)
    failed = sum(1 for r in executed if r is False)
    skipped = sum(1 for r in results if r is None)

    print(f"Testes executados: {len(executed)}/{len(results)}")
    print(f"Passaram: {passed}")
    print(f"Falharam: {failed}")
    print(f"Pulados: {skipped}")

    if failed == 0 and len(executed) > 0:
        print("\n[OK] Todos os testes executados passaram!")
        sys.exit(0)
    elif len(executed) == 0:
        print("\n[AVISO] Nenhum teste foi executado")
        sys.exit(1)
    else:
        print(f"\n[FALHOU] {failed} teste(s) falharam")
        sys.exit(1)
