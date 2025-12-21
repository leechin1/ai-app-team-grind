"""
ML Readiness Checker.

Checks if there's sufficient data to train the ML model.

Requirements:
- Total interactions >= 100
- Verified interactions (quiz + match) >= 30
- At least 3 different topics/tags covered
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from collections import Counter
from core.review_logger import UnifiedReviewLogger


def print_header(title: str):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_ml_readiness():
    """Check if system is ready for ML training"""

    print("\n" + "#" * 70)
    print("#" + " " * 20 + "ML READINESS CHECK" + " " * 20 + "#")
    print("#" * 70)

    # Load logger
    logger = UnifiedReviewLogger()

    print(f"\n[INFO] Loading data from: {logger.log_file_path}")

    # Get statistics
    stats = logger.get_statistics()

    print_header("DATA COLLECTION STATISTICS")

    print(f"\nTotal Interactions: {stats['total_interactions']}")
    print(f"  - Flashcard reviews: {stats['by_type']['flashcard_review']} (confidence: 0.3)")
    print(f"  - Quiz attempts: {stats['by_type']['quiz_attempt']} (confidence: 0.9)")
    print(f"  - Match attempts: {stats['by_type']['match_attempt']} (confidence: 0.85)")

    print(f"\nVerified Interactions: {stats['verified_interactions']}")
    print(f"Self-Reported Interactions: {stats['self_reported_interactions']}")

    print(f"\nOverall Accuracy: {stats['overall_accuracy']}%")

    # Check requirements
    print_header("ML TRAINING REQUIREMENTS")

    requirements = {
        "Total interactions >= 100": stats['total_interactions'] >= 100,
        "Verified interactions >= 30": stats['verified_interactions'] >= 30,
    }

    # Check tag diversity
    interactions = logger.load_interactions()
    all_tags = []
    for interaction in interactions:
        all_tags.extend(interaction.tags)

    unique_tags = set(tag.lower() for tag in all_tags)
    tag_diversity_ok = len(unique_tags) >= 3

    requirements["At least 3 different topics/tags"] = tag_diversity_ok

    # Display requirements
    for requirement, passed in requirements.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {requirement}")

    # Overall readiness
    all_passed = all(requirements.values())

    print_header("READINESS STATUS")

    if all_passed:
        print("\n  STATUS: READY FOR ML TRAINING")
        print("\n  Next steps:")
        print("    1. Run training script: python scripts/train_ml_model.py")
        print("    2. Model will be saved to models/")
        print("    3. ML predictions will be blended with SM-2 (hybrid mode)")

        # Calculate ML confidence
        verified_count = stats['verified_interactions']
        ml_confidence = min(0.8, (verified_count / 100) * 0.8)

        print(f"\n  Initial ML Confidence: {ml_confidence:.1%}")
        print(f"    (Will increase to 80% at 100 verified interactions)")

    else:
        print("\n  STATUS: NOT READY - MORE DATA NEEDED")

        # Calculate remaining requirements
        remaining_total = max(0, 100 - stats['total_interactions'])
        remaining_verified = max(0, 30 - stats['verified_interactions'])
        remaining_tags = max(0, 3 - len(unique_tags))

        print("\n  What's needed:")
        if remaining_total > 0:
            print(f"    - {remaining_total} more total interactions")
        if remaining_verified > 0:
            print(f"    - {remaining_verified} more verified interactions (quizzes/matches)")
        if remaining_tags > 0:
            print(f"    - {remaining_tags} more different topics/tags")

        print("\n  How to collect data:")
        print("    1. Review flashcards using SM-2 system")
        print("    2. Take quizzes (verified data, HIGH confidence)")
        print("    3. Play match quizzes (verified data, HIGH confidence)")
        print("    4. Ensure coverage across different topics")

    # Tag distribution
    if unique_tags:
        print_header("TAG DISTRIBUTION")

        tag_counts = Counter(tag.lower() for tag in all_tags)
        top_tags = tag_counts.most_common(10)

        print(f"\n  Total unique tags: {len(unique_tags)}")
        print("\n  Top 10 tags:")
        for tag, count in top_tags:
            print(f"    - {tag}: {count} interactions")

    # Data quality analysis
    print_header("DATA QUALITY ANALYSIS")

    if stats['verified_interactions'] > 0:
        verified_ratio = stats['verified_interactions'] / stats['total_interactions']
        print(f"\n  Verified Data Ratio: {verified_ratio:.1%}")

        if verified_ratio >= 0.3:
            print("    [GOOD] High proportion of verified data")
        elif verified_ratio >= 0.2:
            print("    [OK] Moderate proportion of verified data")
        else:
            print("    [WARNING] Low verified data - encourage more quizzes/matches")

    # Estimate ML performance
    if all_passed:
        print("\n  Estimated ML Model Performance:")

        # Simple heuristic based on data quantity and quality
        data_score = min(1.0, stats['total_interactions'] / 200)
        quality_score = min(1.0, stats['verified_interactions'] / 50)
        estimated_accuracy = 0.7 + (data_score * 0.1) + (quality_score * 0.15)

        print(f"    Expected accuracy: {estimated_accuracy:.1%}")
        print(f"    (Will improve with more data)")

    print("\n")


if __name__ == "__main__":
    try:
        check_ml_readiness()
    except FileNotFoundError:
        print("\n[ERROR] No data found!")
        print("  Run the spaced repetition system first to collect data.")
        print("  File expected: data/review_events.jsonl")
        print("\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
