"""
Unified Review Logger for Multi-Source Data Collection.

Logs interactions from:
- Flashcard reviews (self-reported, LOW confidence)
- Quiz attempts (verified, HIGH confidence)
- Match quiz attempts (verified, HIGH confidence)

Data is stored in JSONL format for easy processing and ML training.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Literal
from core.models import ReviewInteraction, FlashCard, QuizQuestion, QuizAnswer, MatchPair, MatchQuizAnswer


class UnifiedReviewLogger:
    """
    Logs all user interactions with study materials.

    Supports multi-source data collection with confidence weighting:
    - flashcard_review: confidence_weight = 0.3 (self-reported)
    - quiz_attempt: confidence_weight = 0.9 (verified)
    - match_attempt: confidence_weight = 0.85 (verified)

    Data is stored in JSONL (JSON Lines) format for easy streaming and processing.

    Example usage:
        >>> logger = UnifiedReviewLogger()
        >>> logger.log_flashcard_review(
        ...     flashcard=my_card,
        ...     response_quality=5,
        ...     was_correct=True,
        ...     time_spent=3.5
        ... )
    """

    # Confidence weights for different interaction types
    CONFIDENCE_WEIGHTS = {
        "flashcard_review": 0.3,   # Self-reported (can be biased)
        "quiz_attempt": 0.9,        # Verified (objective correct/incorrect)
        "match_attempt": 0.85       # Verified (objective matching)
    }

    def __init__(self, log_file_path: Optional[str] = None):
        """
        Initialize the logger.

        Args:
            log_file_path: Path to JSONL file (defaults to data/review_events.jsonl)
        """

        if log_file_path is None:
            # Default to data/review_events.jsonl
            project_root = Path(__file__).parent.parent
            data_dir = project_root / "data"
            data_dir.mkdir(exist_ok=True)
            log_file_path = str(data_dir / "review_events.jsonl")

        self.log_file_path = log_file_path

    def log_flashcard_review(
        self,
        flashcard: FlashCard,
        response_quality: int,
        was_correct: bool,
        time_spent_seconds: float
    ) -> ReviewInteraction:
        """
        Log a flashcard review interaction.

        Args:
            flashcard: The flashcard that was reviewed
            response_quality: User's response quality (0-5)
            was_correct: Whether the user answered correctly
            time_spent_seconds: Time spent reviewing (seconds)

        Returns:
            The created ReviewInteraction object
        """

        interaction = ReviewInteraction(
            flashcard_id=flashcard.id,
            interaction_type="flashcard_review",
            user_response_quality=response_quality,
            was_correct=was_correct,
            time_spent_seconds=time_spent_seconds,
            tags=flashcard.tags,
            confidence_weight=self.CONFIDENCE_WEIGHTS["flashcard_review"],
            timestamp=datetime.now()
        )

        self._write_interaction(interaction)
        return interaction

    def log_quiz_attempt(
        self,
        flashcard_id: str,
        question: QuizQuestion,
        user_answer: QuizAnswer,
        was_correct: bool
    ) -> ReviewInteraction:
        """
        Log a quiz attempt interaction.

        Args:
            flashcard_id: ID of related flashcard (linked via tags)
            question: The quiz question
            user_answer: User's answer
            was_correct: Whether the answer was correct

        Returns:
            The created ReviewInteraction object
        """

        # Map quiz correctness to SM-2 quality scale
        # Correct = 5 (perfect), Incorrect = 0 (blackout)
        response_quality = 5 if was_correct else 0

        interaction = ReviewInteraction(
            flashcard_id=flashcard_id,
            interaction_type="quiz_attempt",
            user_response_quality=response_quality,
            was_correct=was_correct,
            time_spent_seconds=user_answer.time_spent_seconds,
            tags=question.concept.split(),  # Extract tags from concept
            confidence_weight=self.CONFIDENCE_WEIGHTS["quiz_attempt"],
            timestamp=user_answer.timestamp,
            related_question_id=question.id
        )

        self._write_interaction(interaction)
        return interaction

    def log_match_attempt(
        self,
        flashcard_id: str,
        pair: MatchPair,
        user_answer: MatchQuizAnswer,
        was_correct: bool
    ) -> ReviewInteraction:
        """
        Log a match quiz attempt interaction.

        Args:
            flashcard_id: ID of related flashcard (linked via tags)
            pair: The match pair
            user_answer: User's matching answer
            was_correct: Whether the match was correct

        Returns:
            The created ReviewInteraction object
        """

        # Map match correctness to SM-2 quality scale
        response_quality = 5 if was_correct else 0

        interaction = ReviewInteraction(
            flashcard_id=flashcard_id,
            interaction_type="match_attempt",
            user_response_quality=response_quality,
            was_correct=was_correct,
            time_spent_seconds=user_answer.time_spent_seconds,
            tags=pair.tags,
            confidence_weight=self.CONFIDENCE_WEIGHTS["match_attempt"],
            timestamp=user_answer.timestamp,
            related_question_id=pair.id
        )

        self._write_interaction(interaction)
        return interaction

    def _write_interaction(self, interaction: ReviewInteraction) -> None:
        """
        Write interaction to JSONL file.

        Args:
            interaction: The interaction to log
        """

        # Convert to dict
        interaction_dict = interaction.model_dump(mode='json')

        # Append to JSONL file
        with open(self.log_file_path, 'a', encoding='utf-8') as f:
            json.dump(interaction_dict, f, ensure_ascii=False)
            f.write('\n')

    def load_interactions(
        self,
        interaction_type: Optional[Literal["flashcard_review", "quiz_attempt", "match_attempt"]] = None,
        flashcard_id: Optional[str] = None,
        since_date: Optional[datetime] = None
    ) -> List[ReviewInteraction]:
        """
        Load interactions from JSONL file with optional filtering.

        Args:
            interaction_type: Filter by interaction type
            flashcard_id: Filter by specific flashcard
            since_date: Only load interactions after this date

        Returns:
            List of ReviewInteraction objects
        """

        if not os.path.exists(self.log_file_path):
            return []

        interactions = []

        with open(self.log_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue

                data = json.loads(line)

                # Apply filters
                if interaction_type and data.get('interaction_type') != interaction_type:
                    continue

                if flashcard_id and data.get('flashcard_id') != flashcard_id:
                    continue

                if since_date:
                    timestamp = datetime.fromisoformat(data['timestamp'])
                    if timestamp < since_date:
                        continue

                # Create ReviewInteraction object
                interaction = ReviewInteraction(**data)
                interactions.append(interaction)

        return interactions

    def get_statistics(self) -> dict:
        """
        Get statistics about logged interactions.

        Returns:
            Dictionary with counts and metrics
        """

        interactions = self.load_interactions()

        total = len(interactions)
        by_type = {
            "flashcard_review": 0,
            "quiz_attempt": 0,
            "match_attempt": 0
        }

        verified_count = 0
        correct_count = 0

        for interaction in interactions:
            by_type[interaction.interaction_type] += 1

            if interaction.interaction_type in ["quiz_attempt", "match_attempt"]:
                verified_count += 1

            if interaction.was_correct:
                correct_count += 1

        return {
            "total_interactions": total,
            "by_type": by_type,
            "verified_interactions": verified_count,
            "self_reported_interactions": total - verified_count,
            "overall_accuracy": round(correct_count / total * 100, 1) if total > 0 else 0,
            "verified_ready_for_ml": verified_count >= 30  # Minimum threshold
        }
