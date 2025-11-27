# -*- coding: utf-8 -*-
"""
Testa extracao de texto de PDFs.
"""

import sys
from pathlib import Path

# Adiciona raiz do projeto ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.document_processor import DocumentProcessor


def test_pdf_extraction():
    """Testa extracao de PDF do repositorio"""
    print("Teste: Extracao de PDF")
    print("-" * 60)

    # Procura PDFs na raiz do projeto
    root_dir = Path(__file__).parent.parent
    pdf_files = list(root_dir.glob("*.pdf"))

    if not pdf_files:
        print("[AVISO] Nenhum PDF encontrado na raiz do projeto")
        print("Coloca um ficheiro PDF na raiz para testar")
        return False

    # Usa o primeiro PDF encontrado
    pdf_path = pdf_files[0]
    print(f"PDF encontrado: {pdf_path.name}")
    print(f"Tamanho: {pdf_path.stat().st_size / 1024:.2f} KB\n")

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

        # Guarda texto extraido (opcional)
        output_file = root_dir / f"extracted_{pdf_path.stem}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.content)
        print(f"\n[OK] Texto extraido guardado em: {output_file.name}")

        print("\n[OK] Teste passou!\n")
        return True

    except Exception as e:
        print(f"[FALHOU] Erro ao processar PDF: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("TESTE DE EXTRACAO DE PDF")
    print("=" * 60)
    print()

    success = test_pdf_extraction()

    print("=" * 60)
    print("RESUMO")
    print("=" * 60)

    if success:
        print("[OK] Teste passou!")
    else:
        print("[FALHOU] Teste falhou")
        sys.exit(1)
