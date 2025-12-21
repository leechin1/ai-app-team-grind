"""
SM-2 Spaced Repetition Algorithm Implementation.

Based on the SuperMemo 2 algorithm by Piotr Wozniak (1988).
Calculates optimal review intervals based on user performance.

References:
- https://www.supermemo.com/en/blog/application-of-a-computer-to-improve-the-results-obtained-in-working-with-the-supermemo-method
"""

from datetime import datetime, timedelta
from typing import List, Optional
from core.models import FlashCard, ResponseQuality, ReviewInteraction


class SM2SpacedRepetition:
    """
    Implements the SM-2 spaced repetition algorithm.

    The algorithm calculates the next review date based on:
    - User's response quality (0-5 scale)
    - Current ease factor (difficulty)
    - Number of consecutive correct reviews

    Example usage:
        >>> sm2 = SM2SpacedRepetition()
        >>> updated_card = sm2.process_review(
        ...     card=my_flashcard,
        ...     response_quality=ResponseQuality.PERFECT_RECALL
        ... )
        >>> print(f"Next review: {updated_card.next_review_date}")
    """

    # Minimum ease factor (prevents cards from becoming too difficult)
    MIN_EASE_FACTOR = 1.3

    def process_review(
        self,
        card: FlashCard,
        response_quality: int,
        review_time: Optional[datetime] = None
    ) -> FlashCard:
        """
        Process a single flashcard review and update SM-2 parameters.

        Args:
            card: The flashcard being reviewed
            response_quality: User's response quality (0-5)
            review_time: When the review happened (defaults to now)

        Returns:
            Updated FlashCard with new interval, ease_factor, etc.

        Raises:
            ValueError: If response_quality not in 0-5 range
        """

        if not 0 <= response_quality <= 5:
            raise ValueError(f"response_quality must be 0-5, got {response_quality}")

        if review_time is None:
            review_time = datetime.now()

        # Update review count
        card.review_count += 1
        card.last_reviewed_at = review_time

        # SM-2 Algorithm
        if response_quality >= 3:
            # Correct response
            self._process_correct_review(card, response_quality)
        else:
            # Incorrect response
            self._process_incorrect_review(card)

        # Calculate next review date
        card.next_review_date = review_time + timedelta(days=card.interval)

        return card

    def _process_correct_review(self, card: FlashCard, quality: int) -> None:
        """
        Process a correct review (quality >= 3).

        Increases interval based on ease factor and updates ease factor.
        """

        # Increment repetition count
        card.repetitions += 1

        # Calculate new interval based on repetition number
        if card.repetitions == 1:
            card.interval = 1  # First correct: review tomorrow
        elif card.repetitions == 2:
            card.interval = 6  # Second correct: review in 6 days
        else:
            # Subsequent reviews: multiply previous interval by ease factor
            card.interval = round(card.interval * card.ease_factor)

        # Update ease factor based on quality
        # Formula: EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        card.ease_factor = card.ease_factor + (
            0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
        )

        # Ensure ease factor doesn't go below minimum
        if card.ease_factor < self.MIN_EASE_FACTOR:
            card.ease_factor = self.MIN_EASE_FACTOR

    def _process_incorrect_review(self, card: FlashCard) -> None:
        """
        Process an incorrect review (quality < 3).

        Resets repetition count and sets interval to 1 day.
        """

        # Reset repetitions (start learning from scratch)
        card.repetitions = 0

        # Review again tomorrow
        card.interval = 1

        # Ease factor stays the same (don't penalize difficulty)

    def get_due_cards(
        self,
        cards: List[FlashCard],
        reference_date: Optional[datetime] = None
    ) -> List[FlashCard]:
        """
        Get all cards that are due for review.

        Args:
            cards: List of flashcards to check
            reference_date: Date to check against (defaults to now)

        Returns:
            List of flashcards due for review, sorted by priority
        """

        if reference_date is None:
            reference_date = datetime.now()

        due_cards = []

        for card in cards:
            # New cards (never reviewed) are always due
            if card.next_review_date is None:
                due_cards.append(card)
            # Cards past their review date are due
            elif card.next_review_date <= reference_date:
                due_cards.append(card)

        # Sort by priority (overdue cards first, then by review date)
        due_cards.sort(key=lambda c: c.next_review_date or datetime.min)

        return due_cards

    def get_review_stats(self, card: FlashCard) -> dict:
        """
        Get statistics about a flashcard's review history.

        Args:
            card: The flashcard to analyze

        Returns:
            Dictionary with review statistics
        """

        stats = {
            "total_reviews": card.review_count,
            "consecutive_correct": card.repetitions,
            "current_interval_days": card.interval,
            "ease_factor": round(card.ease_factor, 2),
            "next_review_date": card.next_review_date.isoformat() if card.next_review_date else None,
            "last_reviewed_at": card.last_reviewed_at.isoformat() if card.last_reviewed_at else None,
        }

        # Calculate days until next review
        if card.next_review_date:
            days_until = (card.next_review_date - datetime.now()).days
            stats["days_until_review"] = max(0, days_until)
        else:
            stats["days_until_review"] = 0

        return stats


def calculate_retention_estimate(ease_factor: float, days_since_review: int) -> float:
    """
    Estimate retention probability based on SM-2 parameters.

    This is a simplified estimation formula (not part of original SM-2).
    Used for ML model comparison and analytics.

    Args:
        ease_factor: Card's ease factor (1.3-2.5)
        days_since_review: Days since last review

    Returns:
        Estimated retention probability (0.0 to 1.0)
    """

    # Simple exponential decay model
    # Higher ease factor = slower decay
    # More days = lower retention

    decay_rate = 0.1 / ease_factor
    retention = 1.0 * (0.95 ** (days_since_review * decay_rate))

    return max(0.0, min(1.0, retention))
