"""
Gemini-powered study tools: flashcards, quizzes, etc.
Designed to work with the Notiq note-taking app.
"""
import base64
from typing import List, Dict, Optional
from google import genai
from google.genai import types


# ──────────────────────────────────────────────────────────────────────────────
# Flashcard Generator
# ──────────────────────────────────────────────────────────────────────────────
class FlashcardGenerator:
    """
    Generate flashcards from notes/PDFs using Gemini with few-shot prompting.
    """
    
    FEW_SHOT_EXAMPLES = """
Example 1:
Input: "Photosynthesis is the process by which plants convert light energy into chemical energy stored in glucose."
Output:
Q: What is photosynthesis?
A: The process by which plants convert light energy into chemical energy stored in glucose.

Q: What type of energy do plants convert during photosynthesis?
A: Light energy is converted into chemical energy.

Example 2:
Input: "The Treaty of Versailles was signed in 1919 and officially ended World War I. It imposed harsh penalties on Germany."
Output:
Q: When was the Treaty of Versailles signed?
A: 1919

Q: What did the Treaty of Versailles do?
A: It officially ended World War I and imposed harsh penalties on Germany.
"""

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
    
    def build_prompt(self, snapshot: Dict) -> List[Dict]:
        """
        Build Gemini contents with few-shot examples for flashcard generation.
        """
        system_instruction = (
            "You are a flashcard generator. Create clear, concise Q&A pairs from study material. "
            "Focus on key concepts, definitions, dates, and important facts. "
            "Format each card as:\nQ: [question]\nA: [answer]\n\n"
        )
        
        header = (
            f"{self.FEW_SHOT_EXAMPLES}\n\n"
            "Now generate flashcards from the following material. "
            "Create 8-15 cards covering the most important concepts.\n\n"
        )
        
        parts = [{"text": header}]
        
        # Add note content
        note_text = snapshot.get("content", "")
        subj = snapshot.get("subject", "General")
        parts.append({"text": f"Subject: {subj}\n\nNotes:\n{note_text}\n"})
        
        # Add images (inline)
        for img in snapshot.get("images", []):
            parts.append({"text": f"[Image: {img.get('name','')}] {img.get('caption','')}"})
            parts.append({
                "inline_data": {
                    "mime_type": img.get("mime", "image/*"),
                    "data": img.get("data_b64", ""),
                }
            })
        
        # Add PDF references
        if snapshot.get("pdfs"):
            pdf_lines = [f"- {p.get('name','')} — {p.get('caption','')}" for p in snapshot["pdfs"]]
            parts.append({"text": "PDFs:\n" + "\n".join(pdf_lines)})
        
        parts.append({"text": "\nGenerate the flashcards now:"})
        
        return [{"role": "user", "parts": parts}]
    
    def generate(self, snapshot: Dict, num_cards: Optional[int] = None) -> str:
        """
        Generate flashcards from a session snapshot.
        Returns formatted markdown with Q&A pairs.
        """
        contents = self.build_prompt(snapshot)
        
        config = types.GenerateContentConfig(
            system_instruction="You are a flashcard generator for study materials.",
            temperature=0.4,
            max_output_tokens=2048,
        )
        
        resp = self.client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=contents,
            config=config,
        )
        
        return (getattr(resp, "text", "") or "").strip()


# ──────────────────────────────────────────────────────────────────────────────
# Quiz Generator
# ──────────────────────────────────────────────────────────────────────────────
class QuizGenerator:
    """
    Generate multiple-choice quizzes from notes/PDFs using Gemini.
    """
    
    FEW_SHOT_EXAMPLES = """
Example 1:
Input: "The mitochondria is known as the powerhouse of the cell because it produces ATP."
Output:
**Question 1:** What is the mitochondria often called?
A) The brain of the cell
B) The powerhouse of the cell ✓
C) The storage unit of the cell
D) The membrane of the cell

**Question 2:** What does the mitochondria produce?
A) DNA
B) Proteins
C) ATP ✓
D) Glucose

Example 2:
Input: "Shakespeare wrote Romeo and Juliet in the late 16th century, around 1594-1596."
Output:
**Question 1:** Who wrote Romeo and Juliet?
A) Charles Dickens
B) William Shakespeare ✓
C) Jane Austen
D) Mark Twain

**Question 2:** When was Romeo and Juliet written?
A) 1400s
B) 1500s ✓
C) 1600s
D) 1700s
"""

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
    
    def build_prompt(self, snapshot: Dict, num_questions: int = 10) -> List[Dict]:
        """
        Build Gemini contents for quiz generation with few-shot examples.
        """
        header = (
            f"{self.FEW_SHOT_EXAMPLES}\n\n"
            f"Now generate a {num_questions}-question multiple choice quiz from the following material. "
            "Mark the correct answer with ✓. Use this format:\n"
            "**Question N:** [question]\n"
            "A) [option]\n"
            "B) [option] ✓\n"
            "C) [option]\n"
            "D) [option]\n\n"
        )
        
        parts = [{"text": header}]
        
        # Add content
        note_text = snapshot.get("content", "")
        subj = snapshot.get("subject", "General")
        parts.append({"text": f"Subject: {subj}\n\nNotes:\n{note_text}\n"})
        
        # Add images
        for img in snapshot.get("images", []):
            parts.append({"text": f"[Image: {img.get('name','')}] {img.get('caption','')}"})
            parts.append({
                "inline_data": {
                    "mime_type": img.get("mime", "image/*"),
                    "data": img.get("data_b64", ""),
                }
            })
        
        # Add PDFs
        if snapshot.get("pdfs"):
            pdf_lines = [f"- {p.get('name','')} — {p.get('caption','')}" for p in snapshot["pdfs"]]
            parts.append({"text": "PDFs:\n" + "\n".join(pdf_lines)})
        
        parts.append({"text": f"\nGenerate the {num_questions}-question quiz now:"})
        
        return [{"role": "user", "parts": parts}]
    
    def generate(self, snapshot: Dict, num_questions: int = 10) -> str:
        """
        Generate a multiple-choice quiz from a session snapshot.
        """
        contents = self.build_prompt(snapshot, num_questions)
        
        config = types.GenerateContentConfig(
            system_instruction="You are a quiz generator for study materials. Create challenging but fair questions.",
            temperature=0.5,
            max_output_tokens=2048,
        )
        
        resp = self.client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=contents,
            config=config,
        )
        
        return (getattr(resp, "text", "") or "").strip()
