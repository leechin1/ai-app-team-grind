"""
Feature Extraction for ML Model Training.

Extracts features from ReviewInteraction data with tag-based cross-source enrichment.
This enables the ML model to learn from quiz/match performance and apply it to flashcard predictions.
"""

from typing import List, Dict, Tuple
from collections import defaultdict
from datetime import datetime
from core.models import FlashCard, ReviewInteraction


class FeatureExtractor:
    """
    Extracts numerical features from flashcards and review history.

    Features include:
    - Card-level: ease_factor, repetitions, difficulty
    - User history: avg accuracy, response times
    - Tag-based: quiz accuracy, match accuracy, consistency across sources
    """

    def __init__(self, interactions: List[ReviewInteraction]):
        """
        Initialize feature extractor with interaction history.

        Args:
            interactions: List of all ReviewInteraction records
        """
        self.interactions = interactions
        self._build_tag_statistics()

    def _build_tag_statistics(self) -> None:
        """
        Build tag-based statistics from interactions.

        This enables cross-source learning:
        - If user scores well on "biology" quizzes, we infer they remember "biology" flashcards
        """

        # Tag -> interaction type -> [was_correct values]
        self.tag_performance: Dict[str, Dict[str, List[bool]]] = defaultdict(
            lambda: defaultdict(list)
        )

        for interaction in self.interactions:
            for tag in interaction.tags:
                tag_lower = tag.lower()
                self.tag_performance[tag_lower][interaction.interaction_type].append(
                    interaction.was_correct
                )

    def extract_features(self, card: FlashCard) -> List[float]:
        """
        Extract feature vector for a flashcard.

        Returns 13 features:
        [0] ease_factor (1.3-2.5)
        [1] repetitions (0-100+)
        [2] days_since_last_review (0-365+)
        [3] difficulty (0=easy, 1=medium, 2=hard)
        [4] review_count (0-100+)
        [5] avg_quiz_accuracy (0.0-1.0, verified HIGH confidence)
        [6] avg_match_accuracy (0.0-1.0, verified HIGH confidence)
        [7] avg_flashcard_accuracy (0.0-1.0, self-reported LOW confidence)
        [8] avg_response_time (0.0-30.0 seconds)
        [9] total_interactions (0-1000+)
        [10] tag_quiz_success_rate (0.0-1.0, cross-source)
        [11] tag_match_success_rate (0.0-1.0, cross-source)
        [12] tag_consistency_score (0.0-1.0, variance across sources)

        Args:
            card: FlashCard to extract features for

        Returns:
            List of 13 numerical features
        """

        features = []

        # [0] Ease factor
        features.append(card.ease_factor)

        # [1] Repetitions
        features.append(float(card.repetitions))

        # [2] Days since last review
        if card.last_reviewed_at:
            days_since = (datetime.now() - card.last_reviewed_at).days
            features.append(float(days_since))
        else:
            features.append(0.0)

        # [3] Difficulty (encoded as 0=easy, 1=medium, 2=hard)
        difficulty_map = {"easy": 0, "medium": 1, "hard": 2}
        features.append(float(difficulty_map.get(card.difficulty.value, 1)))

        # [4] Review count
        features.append(float(card.review_count))

        # Get interactions for this card
        card_interactions = [i for i in self.interactions if i.flashcard_id == card.id]

        # [5-7] Accuracy by interaction type
        quiz_accuracy = self._calculate_accuracy_by_type(card_interactions, "quiz_attempt")
        match_accuracy = self._calculate_accuracy_by_type(card_interactions, "match_attempt")
        flashcard_accuracy = self._calculate_accuracy_by_type(card_interactions, "flashcard_review")

        features.append(quiz_accuracy)
        features.append(match_accuracy)
        features.append(flashcard_accuracy)

        # [8] Average response time
        avg_time = self._calculate_avg_response_time(card_interactions)
        features.append(avg_time)

        # [9] Total interactions
        features.append(float(len(card_interactions)))

        # [10-12] Tag-based cross-source features
        tag_quiz_rate, tag_match_rate, tag_consistency = self._calculate_tag_features(card.tags)
        features.append(tag_quiz_rate)
        features.append(tag_match_rate)
        features.append(tag_consistency)

        return features

    def _calculate_accuracy_by_type(
        self,
        interactions: List[ReviewInteraction],
        interaction_type: str
    ) -> float:
        """Calculate accuracy for specific interaction type."""

        type_interactions = [i for i in interactions if i.interaction_type == interaction_type]

        if not type_interactions:
            return 0.5  # Neutral default

        correct = sum(1 for i in type_interactions if i.was_correct)
        return correct / len(type_interactions)

    def _calculate_avg_response_time(self, interactions: List[ReviewInteraction]) -> float:
        """Calculate average response time."""

        if not interactions:
            return 5.0  # Default 5 seconds

        total_time = sum(i.time_spent_seconds for i in interactions)
        return total_time / len(interactions)

    def _calculate_tag_features(self, tags: List[str]) -> Tuple[float, float, float]:
        """
        Calculate tag-based cross-source features.

        Returns:
            (tag_quiz_success_rate, tag_match_success_rate, tag_consistency_score)
        """

        if not tags:
            return (0.5, 0.5, 0.5)

        quiz_rates = []
        match_rates = []
        flashcard_rates = []

        for tag in tags:
            tag_lower = tag.lower()

            # Quiz success rate for this tag
            quiz_results = self.tag_performance[tag_lower]["quiz_attempt"]
            if quiz_results:
                quiz_rates.append(sum(quiz_results) / len(quiz_results))

            # Match success rate for this tag
            match_results = self.tag_performance[tag_lower]["match_attempt"]
            if match_results:
                match_rates.append(sum(match_results) / len(match_results))

            # Flashcard success rate for this tag
            flashcard_results = self.tag_performance[tag_lower]["flashcard_review"]
            if flashcard_results:
                flashcard_rates.append(sum(flashcard_results) / len(flashcard_results))

        # Average rates across tags
        avg_quiz_rate = sum(quiz_rates) / len(quiz_rates) if quiz_rates else 0.5
        avg_match_rate = sum(match_rates) / len(match_rates) if match_rates else 0.5
        avg_flashcard_rate = sum(flashcard_rates) / len(flashcard_rates) if flashcard_rates else 0.5

        # Consistency score: how similar are quiz/match/flashcard rates?
        # Low variance = consistent knowledge, High variance = uncertain
        all_rates = [r for r in [avg_quiz_rate, avg_match_rate, avg_flashcard_rate] if r != 0.5]

        if len(all_rates) >= 2:
            # Calculate variance
            mean = sum(all_rates) / len(all_rates)
            variance = sum((r - mean) ** 2 for r in all_rates) / len(all_rates)
            consistency = 1.0 - min(1.0, variance * 2)  # Lower variance = higher consistency
        else:
            consistency = 0.5  # Neutral

        return (avg_quiz_rate, avg_match_rate, consistency)

    def get_feature_names(self) -> List[str]:
        """Get names of all features (for debugging/analysis)."""

        return [
            "ease_factor",
            "repetitions",
            "days_since_last_review",
            "difficulty",
            "review_count",
            "avg_quiz_accuracy",
            "avg_match_accuracy",
            "avg_flashcard_accuracy",
            "avg_response_time",
            "total_interactions",
            "tag_quiz_success_rate",
            "tag_match_success_rate",
            "tag_consistency_score"
        ]

    def prepare_dataset(
        self,
        cards: List[FlashCard]
    ) -> Tuple[List[List[float]], List[int], List[float]]:
        """
        Prepare complete dataset for ML training.

        Args:
            cards: List of flashcards with review history

        Returns:
            Tuple of (features, labels, weights):
            - features: List of feature vectors
            - labels: List of binary labels (1=remembered, 0=forgot)
            - weights: Sample weights based on confidence (verified data gets higher weight)
        """

        features_list = []
        labels = []
        weights = []

        for card in cards:
            # Get interactions for this card
            card_interactions = [i for i in self.interactions if i.flashcard_id == card.id]

            if not card_interactions:
                continue

            # Create training sample from most recent interaction
            latest_interaction = max(card_interactions, key=lambda i: i.timestamp)

            # Extract features
            feature_vector = self.extract_features(card)

            # Label: was it remembered?
            label = 1 if latest_interaction.was_correct else 0

            # Weight: confidence of this interaction
            weight = latest_interaction.confidence_weight

            features_list.append(feature_vector)
            labels.append(label)
            weights.append(weight)

        return (features_list, labels, weights)


def get_weighted_sample_counts(weights: List[float]) -> Dict[str, int]:
    """
    Calculate effective sample counts after weighting.

    Args:
        weights: List of sample weights

    Returns:
        Dictionary with weighted counts
    """

    # Count by weight range
    high_confidence = sum(1 for w in weights if w >= 0.8)  # Quiz/match
    low_confidence = sum(1 for w in weights if w < 0.5)    # Flashcard review

    # Effective weighted total
    effective_total = sum(weights)

    return {
        "total_samples": len(weights),
        "high_confidence_samples": high_confidence,
        "low_confidence_samples": low_confidence,
        "effective_weighted_total": round(effective_total, 1)
    }
