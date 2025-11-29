# scripts/generate_study_materials.py

"""
Script de integração completa: Documento → Flashcards + Quiz

Workflow:
1. Recebe documento (PDF, DOCX, imagem, ou texto)
2. Extrai texto (DocumentProcessor)
3. Gera flashcards (AIContentGenerator)
4. Gera quiz (AIContentGenerator)
5. Guarda resultados em JSON

Uso:
    python scripts/generate_study_materials.py <ficheiro>
    python scripts/generate_study_materials.py notas.pdf
    python scripts/generate_study_materials.py screenshot.png
    python scripts/generate_study_materials.py --text "Texto direto..."

Exemplos:
    # Com PDF
    python scripts/generate_study_materials.py biology_notes.pdf
    
    # Com imagem
    python scripts/generate_study_materials.py lecture_slide.jpg
    
    # Com texto direto
    python scripts/generate_study_materials.py --text "A mitocôndria é..."
    
    # Com opções customizadas
    python scripts/generate_study_materials.py notas.pdf --cards 15 --quiz 10
"""

import sys
from pathlib import Path
import argparse
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.document_processor import DocumentProcessor
from core.ai_generator import AIContentGenerator
from core.models import DifficultyLevel
from dotenv import load_dotenv
import os

load_dotenv()


# ============================================================================
# HELPERS
# ============================================================================

def print_banner():
    """Imprime banner bonito"""
    banner = """
======================================================================

        GERADOR DE MATERIAL DE ESTUDO COM IA

        Documento -> Flashcards + Quiz
        Powered by Gemini AI

======================================================================
"""
    print(banner)


def print_step(step_num: int, total: int, message: str):
    """Imprime progresso de step"""
    print(f"\n{'='*70}")
    print(f"[PASSO {step_num}/{total}] {message}")
    print('='*70)


def print_success(message: str):
    """Imprime sucesso"""
    print(f"[OK] {message}")


def print_error(message: str):
    """Imprime erro"""
    print(f"[ERRO] {message}")


def print_info(message: str, indent: int = 0):
    """Imprime informacao"""
    prefix = "   " * indent
    print(f"{prefix}[INFO] {message}")


# ============================================================================
# PROCESSAMENTO
# ============================================================================

def process_document_file(file_path: Path, api_key: str) -> dict:
    """
    Processa ficheiro de documento.
    
    Returns:
        dict com 'content' e 'metadata'
    """
    
    print_info(f"Ficheiro: {file_path.name}")
    print_info(f"Tamanho: {file_path.stat().st_size:,} bytes")
    
    # Lê ficheiro
    with open(file_path, 'rb') as f:
        file_bytes = f.read()
    
    # Processa
    processor = DocumentProcessor(gemini_api_key=api_key)
    result = processor.process_document(file_bytes, file_path.name)
    
    print_success("Documento processado!")
    print_info(f"Tipo: {result.metadata.document_type.value}", indent=1)
    print_info(f"Método: {result.metadata.extraction_method}", indent=1)
    print_info(f"Texto extraído: {result.metadata.extracted_text_length:,} caracteres", indent=1)
    
    if result.metadata.num_pages:
        print_info(f"Páginas: {result.metadata.num_pages}", indent=1)
    
    return {
        'content': result.content,
        'metadata': result.metadata.model_dump()
    }


def process_text_input(text: str) -> dict:
    """
    Processa texto direto.
    
    Returns:
        dict com 'content' e 'metadata'
    """
    
    print_info(f"Texto: {len(text)} caracteres")
    
    processor = DocumentProcessor()
    result = processor.process_text_input(text, "Texto direto")
    
    print_success("Texto processado!")
    
    return {
        'content': result.content,
        'metadata': result.metadata.model_dump()
    }


def generate_flashcards(content: str, num_cards: int, api_key: str, difficulty: str = None) -> dict:
    """
    Gera flashcards.
    
    Returns:
        dict com flashcards e metadados
    """
    
    print_info(f"Número de cards pedidos: {num_cards}")
    if difficulty:
        print_info(f"Dificuldade: {difficulty}")
    
    # Converte difficulty string para enum
    difficulty_filter = None
    if difficulty:
        difficulty_map = {
            'easy': DifficultyLevel.EASY,
            'medium': DifficultyLevel.MEDIUM,
            'hard': DifficultyLevel.HARD
        }
        difficulty_filter = difficulty_map.get(difficulty.lower())
    
    # Gera
    generator = AIContentGenerator(api_key=api_key)
    
    print_info("A chamar Gemini API...", indent=1)
    
    response = generator.generate_flashcards(
        content=content,
        num_cards=num_cards,
        difficulty_filter=difficulty_filter
    )
    
    print_success(f"Gerados {len(response.flashcards)} flashcards!")
    print_info(f"Tempo: {response.generation_time_seconds}s", indent=1)
    print_info(f"Tamanho do conteudo: {response.content_length} chars", indent=1)
    
    return {
        'flashcards': [card.model_dump() for card in response.flashcards],
        'metadata': {
            'total_generated': response.total_generated,
            'generation_time': response.generation_time_seconds,
            'content_length': response.content_length
        }
    }


def generate_quiz(content: str, num_questions: int, api_key: str, difficulty: str = None) -> dict:
    """
    Gera quiz.
    
    Returns:
        dict com questões
    """
    
    print_info(f"Número de questões pedidas: {num_questions}")
    if difficulty:
        print_info(f"Dificuldade: {difficulty}")
    
    # Converte difficulty
    difficulty_filter = None
    if difficulty:
        difficulty_map = {
            'easy': DifficultyLevel.EASY,
            'medium': DifficultyLevel.MEDIUM,
            'hard': DifficultyLevel.HARD
        }
        difficulty_filter = difficulty_map.get(difficulty.lower())
    
    # Gera
    generator = AIContentGenerator(api_key=api_key)
    
    print_info("A chamar Gemini API...", indent=1)
    
    questions = generator.generate_quiz(
        content=content,
        num_questions=num_questions,
        difficulty_filter=difficulty_filter
    )
    
    print_success(f"Geradas {len(questions)} questões!")
    
    return {
        'questions': [q.model_dump() for q in questions],
        'metadata': {
            'total_generated': len(questions)
        }
    }


def save_results(results: dict, output_dir: Path):
    """
    Guarda resultados em ficheiros JSON.
    
    Cria:
    - study_materials_YYYYMMDD_HHMMSS.json (completo)
    - flashcards_YYYYMMDD_HHMMSS.json (só flashcards)
    - quiz_YYYYMMDD_HHMMSS.json (só quiz)
    """
    
    output_dir.mkdir(exist_ok=True)
    
    # Timestamp para nomes de ficheiros
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Ficheiro completo
    complete_file = output_dir / f"study_materials_{timestamp}.json"
    with open(complete_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    print_success(f"Resultado completo: {complete_file}")
    
    # Flashcards separados
    if 'flashcards' in results:
        flashcards_file = output_dir / f"flashcards_{timestamp}.json"
        with open(flashcards_file, 'w', encoding='utf-8') as f:
            json.dump(results['flashcards'], f, indent=2, ensure_ascii=False, default=str)
        print_success(f"Flashcards: {flashcards_file}")
    
    # Quiz separado
    if 'quiz' in results:
        quiz_file = output_dir / f"quiz_{timestamp}.json"
        with open(quiz_file, 'w', encoding='utf-8') as f:
            json.dump(results['quiz'], f, indent=2, ensure_ascii=False, default=str)
        print_success(f"Quiz: {quiz_file}")
    
    return complete_file


def preview_results(results: dict):
    """Mostra preview dos resultados"""

    print("\n" + "="*70)
    print("PREVIEW DOS RESULTADOS")
    print("="*70)

    # Flashcards preview
    if 'flashcards' in results and results['flashcards']['flashcards']:
        print("\nFLASHCARDS (primeiros 3):")
        print("-"*70)

        for i, card in enumerate(results['flashcards']['flashcards'][:3], 1):
            diff = card.get('difficulty', 'unknown').upper()
            print(f"\n{i}. [{diff}]")
            print(f"   Pergunta: {card['front']}")
            print(f"   Resposta: {card['back']}")
            if card.get('tags'):
                print(f"   Tags: {', '.join(card['tags'])}")

        total = len(results['flashcards']['flashcards'])
        if total > 3:
            print(f"\n   ... e mais {total - 3} flashcards")

    # Quiz preview
    if 'quiz' in results and results['quiz']['questions']:
        print("\n\nQUIZ (primeiras 2 questoes):")
        print("-"*70)

        for i, q in enumerate(results['quiz']['questions'][:2], 1):
            print(f"\n{i}. {q['question']}")
            print(f"   Opcoes:")
            for j, opt in enumerate(q['options']):
                marker = "[CORRETO]" if j == q['correct_answer_index'] else "         "
                print(f"      {marker} {chr(65+j)}. {opt}")
            print(f"   Explicacao: {q['explanation']}")

        total = len(results['quiz']['questions'])
        if total > 2:
            print(f"\n   ... e mais {total - 2} questoes")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Função principal"""
    
    # Parse argumentos
    parser = argparse.ArgumentParser(
        description='Gera flashcards e quiz a partir de documentos usando IA',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python scripts/generate_study_materials.py biology.pdf
  python scripts/generate_study_materials.py notes.docx --cards 20 --quiz 15
  python scripts/generate_study_materials.py slide.png
  python scripts/generate_study_materials.py --text "O teu texto aqui..."
  python scripts/generate_study_materials.py lecture.pdf --difficulty easy
        """
    )
    
    # Argumentos
    parser.add_argument(
        'file',
        nargs='?',
        type=str,
        help='Caminho para o ficheiro (PDF, DOCX, imagem, TXT)'
    )
    
    parser.add_argument(
        '--text',
        type=str,
        help='Texto direto em vez de ficheiro'
    )
    
    parser.add_argument(
        '--cards',
        type=int,
        default=10,
        help='Número de flashcards a gerar (default: 10, max: 50)'
    )
    
    parser.add_argument(
        '--quiz',
        type=int,
        default=5,
        help='Número de questões de quiz (default: 5, max: 20)'
    )
    
    parser.add_argument(
        '--difficulty',
        type=str,
        choices=['easy', 'medium', 'hard'],
        help='Filtrar por dificuldade específica'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='output',
        help='Diretório para guardar resultados (default: output/)'
    )
    
    parser.add_argument(
        '--no-quiz',
        action='store_true',
        help='Gerar apenas flashcards (sem quiz)'
    )
    
    parser.add_argument(
        '--no-flashcards',
        action='store_true',
        help='Gerar apenas quiz (sem flashcards)'
    )
    
    args = parser.parse_args()
    
    # Validações
    if not args.file and not args.text:
        parser.error("Fornece um ficheiro ou usa --text")
    
    if args.file and args.text:
        parser.error("Usa ficheiro OU --text, não ambos")
    
    # Banner
    print_banner()
    
    # Verifica API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print_error("GEMINI_API_KEY não configurada!")
        print("\n💡 Solução:")
        print("   1. Cria/edita ficheiro .env")
        print("   2. Adiciona: GEMINI_API_KEY=your_key")
        print("   3. Obtém key: https://aistudio.google.com/app/apikey")
        return 1
    
    print_success(f"API Key configurada: {api_key[:20]}...")
    
    # Resultado final
    results = {
        'timestamp': datetime.now().isoformat(),
        'input': {},
        'flashcards': None,
        'quiz': None
    }
    
    try:
        # =================================================================
        # PASSO 1: Processar Input
        # =================================================================
        
        print_step(1, 4 if not (args.no_quiz or args.no_flashcards) else 3, "Processar Documento/Texto")
        
        if args.file:
            file_path = Path(args.file)
            
            if not file_path.exists():
                print_error(f"Ficheiro não encontrado: {file_path}")
                return 1
            
            doc_result = process_document_file(file_path, api_key)
            results['input'] = {
                'type': 'file',
                'file': str(file_path),
                'metadata': doc_result['metadata']
            }
            content = doc_result['content']
        
        else:  # --text
            doc_result = process_text_input(args.text)
            results['input'] = {
                'type': 'text',
                'length': len(args.text)
            }
            content = doc_result['content']
        
        # Preview do conteudo
        print("\nPreview do conteudo extraido:")
        print("-"*70)
        lines = content.split('\n')
        preview_lines = lines[:10]
        for line in preview_lines:
            print(f"   {line}")
        if len(lines) > 10:
            remaining_lines = len(lines) - 10
            print(f"   ... (+{remaining_lines} linhas)")
        print("-"*70)
        
        # =================================================================
        # PASSO 2: Gerar Flashcards (se não --no-flashcards)
        # =================================================================
        
        if not args.no_flashcards:
            step_num = 2
            total_steps = 3 if args.no_quiz else 4
            
            print_step(step_num, total_steps, f"Gerar {args.cards} Flashcards")
            
            flashcards_result = generate_flashcards(
                content=content,
                num_cards=args.cards,
                api_key=api_key,
                difficulty=args.difficulty
            )
            
            results['flashcards'] = flashcards_result
        
        # =================================================================
        # PASSO 3: Gerar Quiz (se não --no-quiz)
        # =================================================================
        
        if not args.no_quiz:
            if args.no_flashcards:
                step_num = 2
                total_steps = 3
            else:
                step_num = 3
                total_steps = 4
            
            print_step(step_num, total_steps, f"Gerar Quiz com {args.quiz} Questões")
            
            quiz_result = generate_quiz(
                content=content,
                num_questions=args.quiz,
                api_key=api_key,
                difficulty=args.difficulty
            )
            
            results['quiz'] = quiz_result
        
        # =================================================================
        # PASSO 4: Guardar Resultados
        # =================================================================
        
        final_step = 3 if (args.no_quiz or args.no_flashcards) else 4
        print_step(final_step, final_step, "Guardar Resultados")
        
        output_dir = Path(args.output_dir)
        output_file = save_results(results, output_dir)
        
        # =================================================================
        # Preview e Resumo Final
        # =================================================================
        
        preview_results(results)
        
        # Resumo
        print("\n" + "="*70)
        print("[OK] CONCLUIDO COM SUCESSO!")
        print("="*70)

        print("\nResumo:")
        if results['flashcards']:
            print(f"   [OK] Flashcards gerados: {len(results['flashcards']['flashcards'])}")
        if results['quiz']:
            print(f"   [OK] Questoes de quiz: {len(results['quiz']['questions'])}")

        print(f"\nFicheiros guardados em: {output_dir.absolute()}")
        
        print("\n" + "="*70)
        
        return 0
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompido pelo utilizador")
        return 130
    
    except Exception as e:
        print_error(f"Erro fatal: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())