"""
Review Data Analytics Script.

Analyzes collected review data and provides insights.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime, timedelta
from collections import defaultdict, Counter
from core.review_logger import UnifiedReviewLogger


def print_header(title: str):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def analyze_temporal_patterns(logger: UnifiedReviewLogger):
    """Analyze review patterns over time"""

    print_header("TEMPORAL ANALYSIS")

    interactions = logger.load_interactions()

    if not interactions:
        print("\n  No data to analyze yet.")
        return

    # Group by date
    by_date = defaultdict(list)
    for interaction in interactions:
        date_key = interaction.timestamp.date()
        by_date[date_key].append(interaction)

    # Sort dates
    dates = sorted(by_date.keys())

    print(f"\n  Date range: {dates[0]} to {dates[-1]}")
    print(f"  Total days with activity: {len(dates)}")

    # Daily breakdown
    print("\n  Daily Activity:")
    for date in dates[-7:]:  # Last 7 days
        count = len(by_date[date])
        verified = sum(1 for i in by_date[date] if i.interaction_type in ["quiz_attempt", "match_attempt"])
        accuracy = sum(1 for i in by_date[date] if i.was_correct) / count * 100

        print(f"    {date}: {count} interactions ({verified} verified) - {accuracy:.0f}% accuracy")


def analyze_performance_by_type(logger: UnifiedReviewLogger):
    """Analyze performance by interaction type"""

    print_header("PERFORMANCE BY TYPE")

    interactions = logger.load_interactions()

    by_type = defaultdict(list)
    for interaction in interactions:
        by_type[interaction.interaction_type].append(interaction)

    for interaction_type, type_interactions in by_type.items():
        if not type_interactions:
            continue

        total = len(type_interactions)
        correct = sum(1 for i in type_interactions if i.was_correct)
        accuracy = (correct / total * 100) if total > 0 else 0

        avg_time = sum(i.time_spent_seconds for i in type_interactions) / total

        confidence = type_interactions[0].confidence_weight

        print(f"\n  {interaction_type}:")
        print(f"    Total: {total}")
        print(f"    Accuracy: {accuracy:.1f}%")
        print(f"    Avg time: {avg_time:.1f}s")
        print(f"    Confidence weight: {confidence}")


def analyze_tag_performance(logger: UnifiedReviewLogger):
    """Analyze performance by tag"""

    print_header("PERFORMANCE BY TAG")

    interactions = logger.load_interactions()

    # Collect tag performance
    tag_stats = defaultdict(lambda: {"total": 0, "correct": 0, "verified": 0})

    for interaction in interactions:
        for tag in interaction.tags:
            tag_lower = tag.lower()
            tag_stats[tag_lower]["total"] += 1
            if interaction.was_correct:
                tag_stats[tag_lower]["correct"] += 1
            if interaction.interaction_type in ["quiz_attempt", "match_attempt"]:
                tag_stats[tag_lower]["verified"] += 1

    # Sort by total interactions
    sorted_tags = sorted(tag_stats.items(), key=lambda x: x[1]["total"], reverse=True)

    print(f"\n  Total unique tags: {len(sorted_tags)}")
    print("\n  Top 10 tags by activity:")

    for tag, stats in sorted_tags[:10]:
        accuracy = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
        verified_pct = (stats["verified"] / stats["total"] * 100) if stats["total"] > 0 else 0

        print(f"\n    {tag}:")
        print(f"      Interactions: {stats['total']}")
        print(f"      Accuracy: {accuracy:.0f}%")
        print(f"      Verified: {stats['verified']} ({verified_pct:.0f}%)")


def analyze_learning_trends(logger: UnifiedReviewLogger):
    """Analyze learning trends over time"""

    print_header("LEARNING TRENDS")

    interactions = logger.load_interactions()

    if len(interactions) < 10:
        print("\n  Need at least 10 interactions to analyze trends.")
        return

    # Split into first half and second half
    midpoint = len(interactions) // 2
    first_half = interactions[:midpoint]
    second_half = interactions[midpoint:]

    # Calculate accuracy for each half
    first_accuracy = sum(1 for i in first_half if i.was_correct) / len(first_half) * 100
    second_accuracy = sum(1 for i in second_half if i.was_correct) / len(second_half) * 100

    improvement = second_accuracy - first_accuracy

    print(f"\n  First half accuracy: {first_accuracy:.1f}%")
    print(f"  Second half accuracy: {second_accuracy:.1f}%")
    print(f"  Improvement: {improvement:+.1f}%")

    if improvement > 5:
        print("    [GOOD] Learning is improving!")
    elif improvement < -5:
        print("    [WARNING] Performance declining - may need review")
    else:
        print("    [OK] Performance stable")

    # Response time trend
    first_avg_time = sum(i.time_spent_seconds for i in first_half) / len(first_half)
    second_avg_time = sum(i.time_spent_seconds for i in second_half) / len(second_half)

    time_change = second_avg_time - first_avg_time

    print(f"\n  First half avg time: {first_avg_time:.1f}s")
    print(f"  Second half avg time: {second_avg_time:.1f}s")
    print(f"  Change: {time_change:+.1f}s")

    if time_change < -0.5:
        print("    [GOOD] Getting faster (better retention)")
    elif time_change > 0.5:
        print("    [INFO] Taking longer (may indicate harder content)")


def analyze_cross_source_consistency(logger: UnifiedReviewLogger):
    """Analyze consistency across different interaction types"""

    print_header("CROSS-SOURCE CONSISTENCY")

    interactions = logger.load_interactions()

    # Group by flashcard
    by_flashcard = defaultdict(lambda: defaultdict(list))

    for interaction in interactions:
        by_flashcard[interaction.flashcard_id][interaction.interaction_type].append(
            interaction.was_correct
        )

    # Find flashcards with multiple interaction types
    multi_source_cards = {
        fid: types for fid, types in by_flashcard.items()
        if len(types) > 1
    }

    if not multi_source_cards:
        print("\n  No flashcards with multiple interaction types yet.")
        print("  Consistency analysis needs quiz/match data linked to flashcard reviews.")
        return

    print(f"\n  Flashcards with multiple sources: {len(multi_source_cards)}")

    # Analyze consistency
    consistent = 0
    inconsistent = 0

    for fid, types in multi_source_cards.items():
        accuracies = []
        for interaction_type, results in types.items():
            accuracy = sum(results) / len(results) if results else 0
            accuracies.append(accuracy)

        # Check if consistent (within 20% range)
        max_diff = max(accuracies) - min(accuracies)

        if max_diff < 0.2:
            consistent += 1
        else:
            inconsistent += 1

    print(f"\n  Consistent knowledge: {consistent} cards")
    print(f"  Inconsistent knowledge: {inconsistent} cards")

    if consistent + inconsistent > 0:
        consistency_rate = consistent / (consistent + inconsistent) * 100
        print(f"  Consistency rate: {consistency_rate:.0f}%")

        if consistency_rate >= 70:
            print("    [GOOD] Knowledge is consistent across sources")
        elif consistency_rate >= 50:
            print("    [OK] Moderate consistency")
        else:
            print("    [WARNING] Low consistency - may need more practice")


def main():
    """Run all analytics"""

    print("\n" + "#" * 70)
    print("#" + " " * 18 + "REVIEW DATA ANALYTICS" + " " * 19 + "#")
    print("#" * 70)

    try:
        logger = UnifiedReviewLogger()

        stats = logger.get_statistics()

        if stats['total_interactions'] == 0:
            print("\n[INFO] No data collected yet!")
            print("  Start using the spaced repetition system to collect data.")
            print("  Run: python scripts/test_spaced_repetition.py")
            print("\n")
            return

        # Run analyses
        analyze_temporal_patterns(logger)
        analyze_performance_by_type(logger)
        analyze_tag_performance(logger)
        analyze_learning_trends(logger)
        analyze_cross_source_consistency(logger)

        print_header("SUMMARY")
        print(f"\n  Total interactions analyzed: {stats['total_interactions']}")
        print(f"  Verified interactions: {stats['verified_interactions']}")
        print(f"  Overall accuracy: {stats['overall_accuracy']}%")

        if stats['verified_ready_for_ml']:
            print("\n  [OK] System is ready for ML training!")
            print("  Run: python scripts/check_ml_readiness.py")
        else:
            print(f"\n  [INFO] Keep collecting data for ML training")
            print(f"  Need: {max(0, 30 - stats['verified_interactions'])} more verified interactions")

        print("\n")

    except FileNotFoundError:
        print("\n[ERROR] No data found!")
        print("  File expected: data/review_events.jsonl")
        print("\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
