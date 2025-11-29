# -*- coding: utf-8 -*-
"""
Simple test for flashcard generation without emojis.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.ai_generator import AIContentGenerator
from dotenv import load_dotenv
import os

load_dotenv()

def test_flashcard_generation():
    """Test flashcard generation"""
    print("Test: Flashcard Generation")
    print("-" * 60)

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("[SKIP] GEMINI_API_KEY not found in .env")
        return None

    content = """
    A mitocondria e uma organela celular responsavel pela producao de energia.

    Atraves do processo de respiracao celular, a mitocondria converte glucose
    e oxigenio em ATP (adenosina trifosfato), a molecula de energia da celula.

    A mitocondria possui duas membranas: uma externa lisa e uma interna com
    cristas mitocondriais, onde ocorre a fosforilacao oxidativa.
    """

    try:
        generator = AIContentGenerator(api_key=api_key)
        print(f"Generating flashcards from {len(content)} chars...")

        response = generator.generate_flashcards(
            content=content,
            num_cards=5
        )

        print(f"[OK] Generated {response.total_generated} flashcards")
        print(f"     Content length: {response.content_length} chars")
        print(f"     Generation time: {response.generation_time_seconds}s")
        print(f"\nSample flashcard:")
        print(f"  Front: {response.flashcards[0].front}")
        print(f"  Back: {response.flashcards[0].back}")

        return True

    except Exception as e:
        print(f"[FAILED] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_quiz_generation():
    """Test quiz generation"""
    print("\nTest: Quiz Generation")
    print("-" * 60)

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("[SKIP] GEMINI_API_KEY not found in .env")
        return None

    content = """
    A mitocondria e uma organela celular responsavel pela producao de energia.

    Atraves do processo de respiracao celular, a mitocondria converte glucose
    e oxigenio em ATP (adenosina trifosfato), a molecula de energia da celula.
    """

    try:
        generator = AIContentGenerator(api_key=api_key)
        print(f"Generating quiz from {len(content)} chars...")

        questions = generator.generate_quiz(
            content=content,
            num_questions=3
        )

        print(f"[OK] Generated {len(questions)} questions")
        print(f"\nSample question:")
        print(f"  Question: {questions[0].question}")
        print(f"  Options:")
        for i, opt in enumerate(questions[0].options):
            marker = "[X]" if i == questions[0].correct_answer_index else "[ ]"
            print(f"    {marker} {opt}")
        print(f"  Explanation: {questions[0].explanation}")

        return True

    except Exception as e:
        print(f"[FAILED] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("SIMPLE AI GENERATOR TESTS")
    print("=" * 60)
    print()

    results = []
    results.append(test_flashcard_generation())
    results.append(test_quiz_generation())

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    executed = [r for r in results if r is not None]
    passed = sum(1 for r in executed if r is True)
    failed = sum(1 for r in executed if r is False)
    skipped = sum(1 for r in results if r is None)

    print(f"Executed: {len(executed)}/{len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")

    if failed == 0 and len(executed) > 0:
        print("\n[OK] All tests passed!")
        sys.exit(0)
    elif len(executed) == 0:
        print("\n[SKIP] No tests executed")
        sys.exit(1)
    else:
        print(f"\n[FAILED] {failed} test(s) failed")
        sys.exit(1)
