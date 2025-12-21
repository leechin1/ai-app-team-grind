"""
Test script for SM-2 Spaced Repetition system.

This script tests:
1. SM-2 algorithm with simulated reviews
2. UnifiedReviewLogger with multi-source data
3. Integration with FlashCard model
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime, timedelta
from core.models import FlashCard, ResponseQuality, DifficultyLevel
from core.spaced_repetition import SM2SpacedRepetition, calculate_retention_estimate
from core.review_logger import UnifiedReviewLogger


def print_header(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_sm2_algorithm():
    """Test SM-2 algorithm with a single flashcard"""

    print_header("TEST 1: SM-2 Algorithm")

    # Create a test flashcard
    card = FlashCard(
        front="What is the mitochondria?",
        back="The powerhouse of the cell - produces ATP energy",
        difficulty=DifficultyLevel.MEDIUM,
        tags=["biology", "cell", "mitochondria"]
    )

    print(f"\n[OK] Created flashcard: {card.front[:50]}...")
    print(f"     Initial ease_factor: {card.ease_factor}")
    print(f"     Initial interval: {card.interval} days")

    # Initialize SM-2
    sm2 = SM2SpacedRepetition()

    # Simulate review session
    print("\n--- Simulating Review Session ---")

    reviews = [
        (ResponseQuality.PERFECT_RECALL, "First review: Perfect recall"),
        (ResponseQuality.PERFECT_RECALL, "Second review: Still perfect"),
        (ResponseQuality.CORRECT_HESITATION, "Third review: Correct but hesitated"),
        (ResponseQuality.INCORRECT_HARD_RECALL, "Fourth review: Forgot it!"),
        (ResponseQuality.CORRECT_HARD_RECALL, "Fifth review: Relearned, correct but hard"),
    ]

    for i, (quality, description) in enumerate(reviews, 1):
        print(f"\nReview #{i}: {description}")
        print(f"  Response quality: {quality} ({quality.name})")

        # Process review
        card = sm2.process_review(card, quality)

        # Show results
        print(f"  -> Interval: {card.interval} days")
        print(f"  -> Ease factor: {card.ease_factor:.2f}")
        print(f"  -> Repetitions: {card.repetitions}")
        print(f"  -> Next review: {card.next_review_date.strftime('%Y-%m-%d')}")

    # Final stats
    print("\n--- Final Card Statistics ---")
    stats = sm2.get_review_stats(card)
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n[OK] SM-2 algorithm test completed!")
    return card


def test_unified_review_logger(test_card: FlashCard):
    """Test UnifiedReviewLogger with multi-source interactions"""

    print_header("TEST 2: UnifiedReviewLogger (Multi-Source Data)")

    # Initialize logger (will create data/review_events.jsonl)
    logger = UnifiedReviewLogger()

    print(f"\n[OK] Initialized logger")
    print(f"     Log file: {logger.log_file_path}")

    # Log flashcard review (LOW confidence 0.3)
    print("\n--- Logging Flashcard Review (self-reported) ---")
    interaction1 = logger.log_flashcard_review(
        flashcard=test_card,
        response_quality=5,
        was_correct=True,
        time_spent_seconds=3.2
    )
    print(f"  Interaction ID: {interaction1.interaction_id}")
    print(f"  Type: {interaction1.interaction_type}")
    print(f"  Confidence weight: {interaction1.confidence_weight} (LOW - self-reported)")

    # Simulate quiz attempt (HIGH confidence 0.9)
    print("\n--- Logging Quiz Attempt (verified) ---")
    from core.models import QuizQuestion, QuizAnswer

    quiz_q = QuizQuestion(
        question="Which organelle produces ATP?",
        options=["Nucleus", "Mitochondria", "Ribosome", "Golgi"],
        correct_answer_index=1,
        explanation="Mitochondria are the powerhouse of the cell",
        concept="Cell Biology Organelles"
    )

    quiz_ans = QuizAnswer(
        question_id=quiz_q.id,
        user_answer_index=1,  # Correct!
        time_spent_seconds=5.5
    )

    interaction2 = logger.log_quiz_attempt(
        flashcard_id=test_card.id,
        question=quiz_q,
        user_answer=quiz_ans,
        was_correct=True
    )
    print(f"  Interaction ID: {interaction2.interaction_id}")
    print(f"  Type: {interaction2.interaction_type}")
    print(f"  Confidence weight: {interaction2.confidence_weight} (HIGH - verified)")

    # Simulate match quiz attempt (HIGH confidence 0.85)
    print("\n--- Logging Match Quiz Attempt (verified) ---")
    from core.models import MatchPair, MatchQuizAnswer

    match_pair = MatchPair(
        prompt="Powerhouse of the cell",
        answer="Mitochondria",
        tags=["biology", "cell", "mitochondria"]
    )

    match_ans = MatchQuizAnswer(
        pair_id=match_pair.id,
        user_matched_index=0,  # Correct match
        time_spent_seconds=2.8
    )

    interaction3 = logger.log_match_attempt(
        flashcard_id=test_card.id,
        pair=match_pair,
        user_answer=match_ans,
        was_correct=True
    )
    print(f"  Interaction ID: {interaction3.interaction_id}")
    print(f"  Type: {interaction3.interaction_type}")
    print(f"  Confidence weight: {interaction3.confidence_weight} (HIGH - verified)")

    # Get statistics
    print("\n--- Logger Statistics ---")
    stats = logger.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Load and display interactions
    print("\n--- Loaded Interactions ---")
    all_interactions = logger.load_interactions()
    print(f"  Total loaded: {len(all_interactions)}")

    for interaction in all_interactions[-3:]:  # Show last 3
        print(f"\n  [{interaction.interaction_type}]")
        print(f"    Correct: {interaction.was_correct}")
        print(f"    Confidence: {interaction.confidence_weight}")
        print(f"    Tags: {', '.join(interaction.tags)}")

    print("\n[OK] UnifiedReviewLogger test completed!")


def test_get_due_cards():
    """Test getting due cards for review"""

    print_header("TEST 3: Get Due Cards")

    sm2 = SM2SpacedRepetition()

    # Create multiple cards with different states
    cards = []

    # New card (never reviewed)
    card1 = FlashCard(
        front="What is DNA?",
        back="Deoxyribonucleic acid",
        tags=["biology", "genetics"]
    )
    cards.append(card1)

    # Card due today
    card2 = FlashCard(
        front="What is RNA?",
        back="Ribonucleic acid",
        tags=["biology", "genetics"]
    )
    card2.next_review_date = datetime.now()
    cards.append(card2)

    # Card due in 3 days
    card3 = FlashCard(
        front="What is ATP?",
        back="Adenosine triphosphate",
        tags=["biology", "energy"]
    )
    card3.next_review_date = datetime.now() + timedelta(days=3)
    cards.append(card3)

    # Card overdue by 2 days
    card4 = FlashCard(
        front="What is glucose?",
        back="Simple sugar, C6H12O6",
        tags=["biology", "energy"]
    )
    card4.next_review_date = datetime.now() - timedelta(days=2)
    cards.append(card4)

    print(f"\n[OK] Created {len(cards)} test cards")

    # Get due cards
    due_cards = sm2.get_due_cards(cards)

    print(f"\n--- Due Cards (3 out of 4) ---")
    print(f"  Total due: {len(due_cards)}")

    for i, card in enumerate(due_cards, 1):
        status = "NEW" if card.next_review_date is None else "OVERDUE" if card.next_review_date < datetime.now() else "DUE"
        print(f"\n  {i}. [{status}] {card.front}")
        if card.next_review_date:
            days_diff = (datetime.now() - card.next_review_date).days
            print(f"     Next review was: {card.next_review_date.strftime('%Y-%m-%d')} ({days_diff} days ago)")

    print("\n[OK] Get due cards test completed!")


def test_retention_estimate():
    """Test retention probability estimation"""

    print_header("TEST 4: Retention Probability Estimation")

    print("\n--- Testing retention estimates ---")

    # Test different scenarios
    scenarios = [
        (2.5, 0, "Easy card, just reviewed"),
        (2.5, 7, "Easy card, 7 days later"),
        (1.5, 0, "Hard card, just reviewed"),
        (1.5, 7, "Hard card, 7 days later"),
        (2.0, 30, "Medium card, 30 days later"),
    ]

    for ease_factor, days, description in scenarios:
        retention = calculate_retention_estimate(ease_factor, days)
        print(f"\n  {description}")
        print(f"    Ease factor: {ease_factor}")
        print(f"    Days since review: {days}")
        print(f"    Estimated retention: {retention:.1%}")

    print("\n[OK] Retention estimation test completed!")


def main():
    """Run all tests"""

    print("\n" + "#" * 70)
    print("#" + " " * 15 + "SM-2 SPACED REPETITION TEST SUITE" + " " * 15 + "#")
    print("#" * 70)

    try:
        # Test 1: SM-2 Algorithm
        test_card = test_sm2_algorithm()

        # Test 2: UnifiedReviewLogger
        test_unified_review_logger(test_card)

        # Test 3: Get Due Cards
        test_get_due_cards()

        # Test 4: Retention Estimation
        test_retention_estimate()

        # Summary
        print_header("ALL TESTS PASSED!")
        print("\nYou can now:")
        print("  1. Check data/review_events.jsonl for logged interactions")
        print("  2. Integrate SM-2 into your flashcard review workflow")
        print("  3. Start collecting multi-source data (reviews, quizzes, matches)")
        print("  4. Prepare for ML model training (need 100+ interactions)")
        print("\n")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
