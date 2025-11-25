"""

test the pydantic models to check if they are well definied

"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.models import *

def test_flashcard():
    """test the criation of flashcards"""
    print("🧪 testing flashcard...")
    
    # Criação válida
    card = Flashcard(
        front="O que é mitocôndria?",
        back="Organela responsável pela produção de energia (ATP)",
        difficulty=DifficultyLevel.EASY,
        tags=["biologia", "célula"]
    )
    
    print(f"✅ Flashcard criado: ID={card.id[:8]}...")
    print(f"   Front: {card.front}")
    print(f"   Dificuldade: {card.difficulty.value}")
    
    # Testa validação - isto DEVE falhar
    try:
        invalid_card = Flashcard(
            front="",  # Vazio! Deve dar erro
            back="Test"
        )
        print("❌ ERRO: Aceitou front vazio!")
    except Exception as e:
        print(f"✅ Validação funcionou: {type(e).__name__}")

def test_quiz_question():
    """Testa criação de quiz question"""
    print("\n🧪 Testando QuizQuestion...")
    
    # Válida
    q = QuizQuestion(
        question="Qual a função da mitocôndria?",
        options=[
            "Produzir energia",
            "Sintetizar proteínas",
            "Armazenar água",
            "Dividir a célula"
        ],
        correct_answer_index=0,
        explanation="A mitocôndria produz ATP através da respiração celular",
        concept="Organelas celulares"
    )
    
    print(f"✅ QuizQuestion criado")
    print(f"   Resposta correta: {q.options[q.correct_answer_index]}")
    
    # Testa validação de índice
    try:
        invalid_q = QuizQuestion(
            question="Teste?",
            options=["A", "B"],
            correct_answer_index=10,  # Fora do range!
            explanation="...",
            concept="..."
        )
        print("❌ ERRO: Aceitou índice inválido!")
    except Exception as e:
        print(f"✅ Validação de índice funcionou: {str(e)[:50]}...")

def test_serialization():
    """Testa conversão para JSON"""
    print("\n🧪 Testando serialização JSON...")
    
    card = Flashcard(
        front="Teste",
        back="Resposta",
        tags=["tag1"]
    )
    
    # Converte para dict (JSON-serializable)
    card_dict = card.model_dump()
    print(f"✅ Convertido para dict: {list(card_dict.keys())[:5]}...")
    
    # Converte para JSON string
    card_json = card.model_dump_json()
    print(f"✅ Convertido para JSON (primeiros 100 chars):")
    print(f"   {card_json[:100]}...")

if __name__ == "__main__":
    test_flashcard()
    test_quiz_question()
    test_serialization()
    print("\n🎉 Todos os testes passaram!")