
"""
Educational content generator using Gemini API.

This module implements the logic for:
- Generating flashcards from text
- Generating multiple choice quizzes
- Optimized prompt engineering
- Robust output validation
- Retry logic for API failures
"""

from google import genai
import json
import re
import time
from typing import List, Optional
from pydantic import TypeAdapter

from core.models import (
    FlashCard,
    FlashcardGenerationRequest,
    FlashcardGenerationResponse,
    QuizQuestion,
    DifficultyLevel,
    MatchPair,
    MatchQuizGenerationResponse
)
from langfuse import observe


class AIContentGenerator:
    """
    Generates flashcards and quizzes using Gemini API.

    Examples:
        >>> generator = AIContentGenerator(api_key="your_key")
        >>> response = generator.generate_flashcards("Mitochondria...", num_cards=5)
        >>> print(f"Generated {len(response.flashcards)} flashcards")
    """

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        """
        Initialize the generator.

        Args:
            api_key: Gemini API key
            model_name: Model to use (default: gemini-2.5-flash - fast and cheap)
        """
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    # ========================================================================
    # FLASHCARDS GENERATION
    # ========================================================================
    @observe()
    def generate_flashcards(
        self,
        content: str,
        num_cards: int = 10,
        difficulty_filter: Optional[DifficultyLevel] = None,
        focus_topics: Optional[List[str]] = None,
        source_document_id: Optional[str] = None,
        source_document_name: Optional[str] = None,
    ) -> FlashcardGenerationResponse:
        """
        Generate flashcards from educational content.

        Args:
            content: Source text (from PDF, editor, etc)
            num_cards: How many flashcards to generate (1-50)
            difficulty_filter: Filter by specific difficulty
            focus_topics: List of topics to focus on
            source_document_id: ID of source document
            source_document_name: Name of source document

        Returns:
            FlashcardGenerationResponse with validated flashcards and metadata

        Raises:
            ValueError: If content too short or generation fails
        """

        start_time = time.time()

        # Validation
        if len(content.strip()) < 50:
            raise ValueError(
                f"Content too short to generate flashcards. "
                f"Minimum 50 characters, received: {len(content)}"
            )

        if not 1 <= num_cards <= 50:
            raise ValueError("num_cards must be between 1 and 50")

        print(f"Generating {num_cards} flashcards...")

        # Build prompt
        prompt = self._build_flashcard_prompt(
            content=content,
            num_cards=num_cards,
            difficulty_filter=difficulty_filter,
            focus_topics=focus_topics
        )

        flashcard_schema = TypeAdapter(List[FlashCard]).json_schema()
        # Call Gemini
        raw_response = self._call_gemini_with_retry(prompt=prompt, response_schema=flashcard_schema)

        # Parse JSON
        flashcards_data = json.loads(raw_response)

        # Validate and create Flashcard objects
        flashcards = []
        warnings = []

        for i, card_data in enumerate(flashcards_data):
            try:
                # Add source metadata
                card_data['source_document_id'] = source_document_id
                card_data['source_document_name'] = source_document_name

                # Validate with Pydantic
                flashcard = FlashCard(**card_data)
                flashcards.append(flashcard)

            except Exception as e:
                warning = f"Card {i+1} invalid: {str(e)[:80]}"
                warnings.append(warning)
                print(f"   [WARNING] {warning}")

        # Check that at least some were generated
        if len(flashcards) == 0:
            raise ValueError(
                "No valid flashcards were generated. "
                "Try with different content or fewer cards."
            )

        if len(flashcards) < num_cards // 2:
            warnings.append(
                f"Only {len(flashcards)} of {num_cards} valid cards"
            )

        # Calculate metadata
        generation_time = time.time() - start_time
        estimated_reading_time = len(content) / 1000 * 4  # ~250 words/min

        # Identify topics
        identified_topics = list(set(
            tag
            for card in flashcards
            for tag in card.tags
        ))

        print(f"[OK] Generated {len(flashcards)} flashcards in {generation_time:.1f}s")

        # Return response (using only fields defined in FlashcardGenerationResponse model)
        return FlashcardGenerationResponse(
            flashcards=flashcards,
            total_generated=len(flashcards),
            content_length=len(content),
            generation_time_seconds=round(generation_time, 2)
        )

    def _build_flashcard_prompt(
        self,
        content: str,
        num_cards: int,
        difficulty_filter: Optional[DifficultyLevel],
        focus_topics: Optional[List[str]]
    ) -> str:
        """Build optimized prompt for generating flashcards"""

        # Difficulty instructions
        if difficulty_filter:
            difficulty_instruction = f"\n- All cards must have difficulty: {difficulty_filter.value}"
        else:
            difficulty_instruction = "\n- Vary difficulty (easy/medium/hard) in a balanced way"

        # Topics instructions
        topics_instruction = ""
        if focus_topics:
            topics_str = ", ".join(focus_topics)
            topics_instruction = f"\n- Focus especially on these topics: {topics_str}"

        # Truncate if too long (token limit)
        max_content_length = 8000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n\n[... content truncated ...]"

        # Structured prompt
        prompt = f"""
You are an expert in creating high-quality educational material.

TASK: Create {num_cards} educational flashcards based on the content below.

SOURCE CONTENT:
{content}

IMPORTANT INSTRUCTIONS:
- Each flashcard should test ONE specific concept
- Front (question): Clear, concise, unambiguous (max 100 characters)
- Back (answer): Complete but succinct, don't copy literal text (max 300 characters)
- Tags: Identify 1-3 relevant tags (e.g., ["biology", "cell", "organelles"])
- Difficulty:
  * easy - simple definitions, basic facts
  * medium - relationships between concepts, processes
  * hard - analysis, application, complex comparisons{difficulty_instruction}{topics_instruction}
- Vary question types: "What is...", "What's the function of...", "How...", "Difference between..."
- DO NOT invent information not in the content
- DO NOT use true/false questions
- BE specific and precise

Return the requested flashcards

"""

        return prompt

    # ========================================================================
    # QUIZ GENERATION
    # ========================================================================
    @observe()
    def generate_quiz(
        self,
        content: str,
        num_questions: int = 5,
        difficulty_filter: Optional[DifficultyLevel] = None,
        focus_topics: Optional[List[str]] = None
    ) -> List[QuizQuestion]:
        """
        Generate multiple choice quiz (always 4 options).

        Args:
            content: Source text
            num_questions: How many questions (1-20)
            difficulty_filter: Difficulty filter
            focus_topics: Specific topics

        Returns:
            List of validated QuizQuestions

        Raises:
            ValueError: If content too short or generation fails
        """

        # Validation
        if len(content.strip()) < 50:
            raise ValueError("Content too short to generate quiz")

        if not 1 <= num_questions <= 20:
            raise ValueError("num_questions must be between 1 and 20")

        print(f"Generating {num_questions} quiz questions...")

        # Build prompt
        prompt = self._build_quiz_prompt(
            content=content,
            num_questions=num_questions,
            difficulty_filter=difficulty_filter,
            focus_topics=focus_topics
        )

        quiz_schema = TypeAdapter(List[QuizQuestion]).json_schema()

        # Call Gemini
        raw_response = self._call_gemini_with_retry(prompt=prompt, response_schema=quiz_schema)

        # Parse JSON
        questions_data = json.loads(raw_response)

        # Validate and create QuizQuestion objects
        questions = []

        for i, q_data in enumerate(questions_data):
            try:
                # Pydantic will automatically validate:
                # - Exactly 4 options
                # - correct_answer_index between 0-3
                # - No duplicates, etc
                question = QuizQuestion(**q_data)
                questions.append(question)

            except Exception as e:
                print(f"   [WARNING] Question {i+1} invalid: {str(e)[:80]}")

        if len(questions) == 0:
            raise ValueError("No valid questions were generated")

        print(f"[OK] Generated {len(questions)} valid questions")

        return questions

    def _build_quiz_prompt(
        self,
        content: str,
        num_questions: int,
        difficulty_filter: Optional[DifficultyLevel],
        focus_topics: Optional[List[str]]
    ) -> str:
        """Build prompt for generating quiz"""

        # Difficulty instructions
        if difficulty_filter:
            difficulty_instruction = f"\n- All questions: difficulty {difficulty_filter.value}"
        else:
            difficulty_instruction = "\n- Vary difficulty in a balanced way"

        # Topics instructions
        topics_instruction = ""
        if focus_topics:
            topics_str = ", ".join(focus_topics)
            topics_instruction = f"\n- Focus on these topics: {topics_str}"

        # Truncate if necessary
        max_length = 8000
        if len(content) > max_length:
            content = content[:max_length] + "\n\n[... truncated ...]"

        prompt = f"""
You are an expert in creating educational assessments.

TASK: Create {num_questions} multiple choice questions based on the content.

SOURCE CONTENT:
{content}

CRITICAL INSTRUCTIONS:
- Each question MUST have EXACTLY 4 options (no more, no less)
- Only ONE correct answer per question
- Incorrect options (distractors) must be:
  * Plausible (based on common misconceptions)
  * Clearly wrong for those who know the content
  * Not absurd or obvious
- Question: Clear, complete, unambiguous
- Explanation: 2-3 sentences explaining why the answer is correct
- Concept: Main concept being tested (e.g., "Cell organelles")
- Difficulty:{difficulty_instruction}{topics_instruction}
- Vary types: definitions, application, comparison, cause-effect
- DO NOT use "all of the above" or "none of the above"
- DO NOT invent information not in the content
- Options should have similar length (don't give hints)

"""

        return prompt

    # ========================================================================
    # MATCH QUIZ GENERATION (Flashcard Matching)
    # ========================================================================
    @observe()
    def generate_match_quiz(
        self,
        content: str,
        num_pairs: int = 5,
        difficulty_filter: Optional[DifficultyLevel] = None,
        focus_topics: Optional[List[str]] = None
    ) -> MatchQuizGenerationResponse:
        """
        Generate match quiz (matching pairs) for the user to match.

        Args:
            content: Source text
            num_pairs: How many pairs to generate (1-15)
            difficulty_filter: Difficulty filter
            focus_topics: Specific topics

        Returns:
            MatchQuizGenerationResponse with validated pairs

        Raises:
            ValueError: If content too short or generation fails
        """

        start_time = time.time()

        # Validation
        if len(content.strip()) < 50:
            raise ValueError("Content too short to generate match quiz")

        if not 1 <= num_pairs <= 15:
            raise ValueError("num_pairs must be between 1 and 15")

        print(f"Generating {num_pairs} pairs for match quiz...")

        # Build prompt
        prompt = self._build_match_quiz_prompt(
            content=content,
            num_pairs=num_pairs,
            difficulty_filter=difficulty_filter,
            focus_topics=focus_topics
        )

        # Create schema
        match_schema = TypeAdapter(List[MatchPair]).json_schema()

        # Call Gemini
        raw_response = self._call_gemini_with_retry(
            prompt=prompt,
            response_schema=match_schema
        )

        # Parse JSON
        pairs_data = json.loads(raw_response)

        # Validate and create MatchPair objects
        pairs = []

        for i, pair_data in enumerate(pairs_data):
            try:
                pair = MatchPair(**pair_data)
                pairs.append(pair)
            except Exception as e:
                print(f"   [WARNING] Pair {i+1} invalid: {str(e)[:80]}")

        if len(pairs) == 0:
            raise ValueError("No valid pairs were generated")

        generation_time = time.time() - start_time

        print(f"[OK] Generated {len(pairs)} valid pairs in {generation_time:.1f}s")

        return MatchQuizGenerationResponse(
            pairs=pairs,
            total_pairs=len(pairs),
            content_length=len(content),
            generation_time_seconds=round(generation_time, 2)
        )

    def _build_match_quiz_prompt(
        self,
        content: str,
        num_pairs: int,
        difficulty_filter: Optional[DifficultyLevel],
        focus_topics: Optional[List[str]]
    ) -> str:
        """Build prompt for generating match quiz"""

        # Difficulty instructions
        if difficulty_filter:
            difficulty_instruction = f"\n- All pairs: difficulty {difficulty_filter.value}"
        else:
            difficulty_instruction = "\n- Vary difficulty in a balanced way"

        # Topics instructions
        topics_instruction = ""
        if focus_topics:
            topics_str = ", ".join(focus_topics)
            topics_instruction = f"\n- Focus on these topics: {topics_str}"

        # Truncate if necessary
        max_length = 8000
        if len(content) > max_length:
            content = content[:max_length] + "\n\n[... truncated ...]"

        prompt = f"""
You are an expert in creating interactive educational material.

TASK: Create {num_pairs} matching pairs (prompt + answer) based on the content.

SOURCE CONTENT:
{content}

CRITICAL INSTRUCTIONS:
- Each pair consists of:
  * prompt: Term, concept or short question (max 100 characters)
  * answer: Definition, explanation or response (max 300 characters)
- Pairs must be DISTINCT and NOT ambiguous
- Each prompt should have only ONE obvious correct answer
- Avoid pairs that could have multiple valid answers
- Tags: 1-3 relevant tags for categorization
- hint (optional): A subtle hint if the concept is difficult{difficulty_instruction}{topics_instruction}
- DO NOT invent information not in the content
- Vary types: definitions, functions, characteristics, relationships

EXAMPLES of good pairs:
- prompt: "Organelle responsible for energy (ATP) production"
  answer: "Mitochondria"

- prompt: "Process of nuclear division"
  answer: "Mitosis"

Return the requested pairs.
"""

        return prompt

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    
    def _call_gemini_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        response_schema: Optional[dict] = None
    ) -> str:
        """
        Call Gemini with retry logic for temporary failures.

        Implements exponential backoff:
        - Attempt 1: immediate
        - Attempt 2: wait 1s
        - Attempt 3: wait 2s
        - Attempt 4: wait 4s
        """

        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config={"response_mime_type": "application/json",
                            "response_schema": response_schema

                    }
                )

                if not response.text:
                    raise ValueError("Gemini returned empty response")

                return response.text

            except Exception as e:
                error_msg = str(e)
                print(f"   [WARNING] Attempt {attempt + 1}/{max_retries} failed: {error_msg[:80]}")

                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    print(f"     waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    # Last attempt failed
                    raise Exception(
                        f"Gemini API failed after {max_retries} attempts. "
                        f"Last error: {error_msg}"
                    )

    def _parse_json_response(self, raw_text: str) -> list:
        """
        Clean and parse JSON response from Gemini.

        Handles:
        - Markdown code blocks (```json)
        - Extra text before/after JSON
        - Whitespace
        """

        # Remove markdown code blocks
        clean_text = re.sub(r'```json\s*', '', raw_text)
        clean_text = re.sub(r'```\s*', '', clean_text)

        # Find JSON start ([ or {)
        json_start = -1
        for i, char in enumerate(clean_text):
            if char in '[{':
                json_start = i
                break

        if json_start == -1:
            raise ValueError(
                "No valid JSON found in response. "
                f"Response: {raw_text[:200]}..."
            )

        # Find JSON end (] or })
        json_end = -1
        for i in range(len(clean_text) - 1, -1, -1):
            if clean_text[i] in ']}':
                json_end = i + 1
                break

        if json_end == -1:
            raise ValueError("Incomplete JSON in response")

        # Extract only JSON
        json_text = clean_text[json_start:json_end].strip()

        # Parse
        try:
            parsed = json.loads(json_text)

            if not isinstance(parsed, list):
                raise ValueError(f"Expected list, received {type(parsed).__name__}")

            if len(parsed) == 0:
                raise ValueError("JSON list is empty")

            return parsed

        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON:")
            print(f"   {str(e)}")
            print(f"   Problematic JSON:")
            print(f"   {json_text[:300]}...")
            raise ValueError(f"Invalid JSON: {str(e)}")

    def _assess_content_difficulty(
        self,
        flashcards: List[FlashCard]
    ) -> Optional[DifficultyLevel]:
        """
        Assess overall content difficulty based on flashcards.

        Logic:
        - If >50% are hard → content is hard
        - If >50% are easy → content is easy
        - Otherwise → medium
        """
        if not flashcards:
            return None

        difficulty_counts = {
            DifficultyLevel.EASY: 0,
            DifficultyLevel.MEDIUM: 0,
            DifficultyLevel.HARD: 0
        }

        for card in flashcards:
            difficulty_counts[card.difficulty] += 1

        total = len(flashcards)

        if difficulty_counts[DifficultyLevel.HARD] > total * 0.5:
            return DifficultyLevel.HARD
        elif difficulty_counts[DifficultyLevel.EASY] > total * 0.5:
            return DifficultyLevel.EASY
        else:
            return DifficultyLevel.MEDIUM
