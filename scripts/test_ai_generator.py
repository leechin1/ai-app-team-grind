# scripts/test_ai_generator.py

"""
Teste completo do AIContentGenerator (Gemini Integration).

Testa:
- Geração de flashcards
- Geração de quizzes
- Diferentes dificuldades
- Validações
- Error handling

Executa: python scripts/test_ai_generator.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.ai_generator import AIContentGenerator
from core.models import DifficultyLevel
from dotenv import load_dotenv
import os
import json

load_dotenv()


def print_header(title: str):
    """Helper para headers"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_section(title: str):
    """Helper para secções"""
    print(f"\n🧪 {title}")
    print("-"*70)


# ============================================================================
# CONTEÚDO DE TESTE
# ============================================================================

SAMPLE_CONTENT = """
A Célula Eucariota

As células eucarióticas são células complexas que possuem núcleo definido
delimitado por membrana nuclear, ao contrário das células procarióticas.

Principais Organelas:

1. Núcleo
   - Contém DNA organizado em cromossomas
   - Controla as atividades celulares
   - Local de síntese de RNA

2. Mitocôndria
   - Responsável pela produção de energia (ATP)
   - Possui DNA próprio (herança materna)
   - Respiração celular ocorre aqui
   - Teoria endossimbiótica explica origem

3. Retículo Endoplasmático
   - RE Rugoso: síntese de proteínas (tem ribossomas)
   - RE Liso: síntese de lípidos, metabolismo

4. Complexo de Golgi
   - Modifica, empacota e distribui proteínas
   - Forma vesículas de secreção

5. Lisossomas
   - Digestão intracelular
   - Contêm enzimas digestivas
   - pH ácido interno

6. Cloroplastos (células vegetais)
   - Fotossíntese
   - Convertem luz em energia química
   - Possuem clorofila

Diferenças Eucariotas vs Procariotas:
- Eucariotas: núcleo definido, organelas membranosas, maiores
- Procariotas: sem núcleo, sem organelas, menores, mais simples

Exemplos de células eucarióticas:
- Células animais
- Células vegetais
- Fungos
- Protistas (algas, protozoários)
"""


# ============================================================================
# TESTES
# ============================================================================

def test_flashcard_generation():
    """TESTE 1: Geração básica de flashcards"""
    print_section("TESTE 1: Geração de Flashcards")
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY não configurada no .env")
        return False
    
    try:
        generator = AIContentGenerator(api_key=api_key)
        
        print("   📤 Enviando conteúdo para Gemini...")
        print(f"   📊 Conteúdo: {len(SAMPLE_CONTENT)} caracteres")
        
        response = generator.generate_flashcards(
            content=SAMPLE_CONTENT,
            num_cards=8,
            source_document_name="Biologia - Células"
        )
        
        print(f"\n✅ Sucesso!")
        print(f"   📊 Flashcards gerados: {response.total_generated}")
        print(f"   ⏱️  Tempo de geração: {response.generation_time_seconds}s")
        print(f"   📏 Tamanho do conteudo: {response.content_length} chars")
        
        # Mostra alguns flashcards
        print(f"\n   📇 Exemplos de flashcards gerados:")
        for i, card in enumerate(response.flashcards[:3], 1):
            print(f"\n   Card {i} [{card.difficulty.value.upper()}]:")
            print(f"      ❓ {card.front}")
            print(f"      ✅ {card.back}")
            if card.tags:
                print(f"      🏷️  {', '.join(card.tags)}")
        
        if len(response.flashcards) > 3:
            print(f"\n   ... e mais {len(response.flashcards) - 3} cards")
        
        # Guarda resultado
        output_file = "generated_flashcards.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            flashcards_data = [card.model_dump() for card in response.flashcards]
            json.dump(flashcards_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n   💾 Flashcards guardados em: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_quiz_generation():
    """TESTE 2: Geração de quiz"""
    print_section("TESTE 2: Geração de Quiz")
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY não configurada")
        return False
    
    try:
        generator = AIContentGenerator(api_key=api_key)
        
        print("   📤 Gerando quiz...")
        
        questions = generator.generate_quiz(
            content=SAMPLE_CONTENT,
            num_questions=5
        )
        
        print(f"\n✅ Sucesso!")
        print(f"   📊 Questões geradas: {len(questions)}")
        
        # Mostra as questões
        print(f"\n   📝 Questões do quiz:")
        for i, q in enumerate(questions, 1):
            print(f"\n   Questão {i}:")
            print(f"      {q.question}")
            print(f"      Opções:")
            for j, opt in enumerate(q.options):
                marker = "✅" if j == q.correct_answer_index else "  "
                print(f"         {marker} {j+1}. {opt}")
            print(f"      💡 Explicação: {q.explanation}")
            print(f"      📚 Conceito: {q.concept}")
        
        # Guarda resultado
        output_file = "generated_quiz.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            quiz_data = [q.model_dump() for q in questions]
            json.dump(quiz_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n   💾 Quiz guardado em: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_difficulty_filter():
    """TESTE 3: Filtro de dificuldade"""
    print_section("TESTE 3: Filtro de Dificuldade")
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ Falta API key")
        return False
    
    try:
        generator = AIContentGenerator(api_key=api_key)
        
        print("   📤 Gerando apenas cards EASY...")
        
        response = generator.generate_flashcards(
            content=SAMPLE_CONTENT,
            num_cards=5,
            difficulty_filter=DifficultyLevel.EASY
        )
        
        # Verifica que todos são EASY
        all_easy = all(card.difficulty == DifficultyLevel.EASY for card in response.flashcards)
        
        if all_easy:
            print(f"✅ Todos os {len(response.flashcards)} cards são EASY!")
        else:
            difficulties = [card.difficulty.value for card in response.flashcards]
            print(f"⚠️  Nem todos são EASY. Distribuição: {difficulties}")
        
        # Mostra um exemplo
        if response.flashcards:
            card = response.flashcards[0]
            print(f"\n   Exemplo:")
            print(f"      ❓ {card.front}")
            print(f"      ✅ {card.back}")
        
        return all_easy
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False


def test_focus_topics():
    """TESTE 4: Foco em tópicos específicos"""
    print_section("TESTE 4: Foco em Tópicos Específicos")
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ Falta API key")
        return False
    
    try:
        generator = AIContentGenerator(api_key=api_key)
        
        print("   📤 Gerando cards focados em 'mitocôndria' e 'energia'...")
        
        response = generator.generate_flashcards(
            content=SAMPLE_CONTENT,
            num_cards=5,
            focus_topics=["mitocôndria", "energia", "ATP"]
        )
        
        print(f"✅ Gerados {len(response.flashcards)} cards")
        
        # Verifica se os tópicos aparecem
        for i, card in enumerate(response.flashcards[:3], 1):
            mitocondria_mentioned = any(
                term in (card.front + card.back).lower() 
                for term in ["mitocôndria", "mitocondrial", "energia", "atp"]
            )
            marker = "✅" if mitocondria_mentioned else "⚠️ "
            print(f"\n   {marker} Card {i}:")
            print(f"      {card.front}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False


def test_validations():
    """TESTE 5: Validações de erro"""
    print_section("TESTE 5: Validações")
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ Falta API key")
        return False
    
    generator = AIContentGenerator(api_key=api_key)
    tests_passed = 0
    
    # 5.1: Conteúdo muito curto
    print("   🔍 5.1 - Conteúdo muito curto (deve rejeitar)")
    try:
        generator.generate_flashcards("abc", num_cards=5)
        print("      ❌ ERRO: Aceitou conteúdo muito curto!")
    except ValueError as e:
        print(f"      ✅ Validação funcionou: {str(e)[:60]}...")
        tests_passed += 1
    
    # 5.2: Número inválido de cards
    print("\n   🔍 5.2 - Número inválido de cards (deve rejeitar)")
    try:
        generator.generate_flashcards(SAMPLE_CONTENT, num_cards=100)
        print("      ❌ ERRO: Aceitou 100 cards!")
    except ValueError as e:
        print(f"      ✅ Validação funcionou: {str(e)[:60]}...")
        tests_passed += 1
    
    # 5.3: Quiz com poucas questões
    print("\n   🔍 5.3 - Quiz com número inválido (deve rejeitar)")
    try:
        generator.generate_quiz(SAMPLE_CONTENT, num_questions=0)
        print("      ❌ ERRO: Aceitou 0 questões!")
    except ValueError as e:
        print(f"      ✅ Validação funcionou: {str(e)[:60]}...")
        tests_passed += 1
    
    print(f"\n   📊 Validações: {tests_passed}/3 passaram")
    return tests_passed == 3


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Executa todos os testes"""
    
    print_header("TESTE COMPLETO - AI CONTENT GENERATOR (GEMINI)")
    
    # Verifica API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("\n❌ ERRO CRÍTICO: GEMINI_API_KEY não configurada!")
        print("\n💡 Solução:")
        print("   1. Cria/edita ficheiro .env na raiz do projeto")
        print("   2. Adiciona: GEMINI_API_KEY=your_actual_key_here")
        print("   3. Obtém key em: https://aistudio.google.com/app/apikey")
        return 1
    
    print(f"\n✅ API Key configurada: {api_key[:20]}...")
    
    # Lista de testes
    tests = [
        ("Flashcard Generation", test_flashcard_generation),
        ("Quiz Generation", test_quiz_generation),
        ("Difficulty Filter", test_difficulty_filter),
        ("Focus Topics", test_focus_topics),
        ("Validations", test_validations)
    ]
    
    results = {"passed": 0, "failed": 0}
    
    # Executa testes
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                results["passed"] += 1
            else:
                results["failed"] += 1
        except Exception as e:
            print(f"\n❌ Teste '{test_name}' crashou: {str(e)}")
            results["failed"] += 1
            import traceback
            traceback.print_exc()
    
    # Resumo
    print_header("RESUMO")
    
    total = results["passed"] + results["failed"]
    print(f"\n📊 Resultados:")
    print(f"   ✅ Passaram:  {results['passed']}/{total}")
    print(f"   ❌ Falharam:  {results['failed']}/{total}")
    
    if results["failed"] == 0:
        print(f"\n🎉 TODOS OS TESTES PASSARAM!")
        print(f"\n💡 Ficheiros gerados:")
        print(f"   - generated_flashcards.json")
        print(f"   - generated_quiz.json")
        print(f"\n📚 Próximos passos:")
        print(f"   1. Verifica os ficheiros JSON gerados")
        print(f"   2. Testa com teu próprio conteúdo")
        print(f"   3. Integra com Document Processor")
        print(f"   4. Prepara para API (FastAPI)")
    else:
        print(f"\n⚠️  Alguns testes falharam. Verifica os erros acima.")
    
    print("\n" + "="*70)
    
    return 0 if results["failed"] == 0 else 1


if __name__ == "__main__":
    exit(main())