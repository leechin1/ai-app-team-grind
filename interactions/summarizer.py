"""
Gemini-powered summarization for Notiq notes.
"""
from typing import Dict, List
from google import genai
from google.genai import types


class NoteSummarizer:
    """
    Generate smart summaries from notes using Gemini.
    """
    
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
    
    def build_prompt(self, snapshot: Dict) -> List[Dict]:
        """
        Build Gemini contents for summarization.
        """
        header = (
            "You are a study buddy enhancing note-taking layouts into smart formats.\n"
            "Summarize the entire session (notes + images + PDFs), extract key points, action items, definitions, and a clean outline.\n"
            "Return Markdown with:\n"
            "1) Executive summary\n"
            "2) Bullet key takeaways\n"
            "3) Action items (checkbox list)\n"
            "4) Glossary (term → definition)\n"
            "5) References (list attached assets)\n"
            "Keep it concise and well-structured."
        )

        parts = [{"text": header}]

        note_text = snapshot.get("content", "")
        subj = snapshot.get("subject", "General")
        parts.append({"text": f"Subject: {subj}\n\nFull note content:\n{note_text}\n"})

        # Inline images
        for img in snapshot.get("images", []):
            parts.append({"text": f"[Image: {img.get('name','(unnamed)')}] Caption: {img.get('caption','')}"})
            parts.append({
                "inline_data": {
                    "mime_type": img.get("mime", "image/*"),
                    "data": img.get("data_b64", ""),
                }
            })

        # PDFs (names + captions only)
        if snapshot.get("pdfs"):
            pdf_lines = []
            for p in snapshot["pdfs"]:
                pdf_lines.append(f"- {p.get('name','(unnamed)')} — {p.get('caption','')}".strip())
            parts.append({"text": "Attached PDFs (names & notes only; content not embedded to save tokens):\n" + "\n".join(pdf_lines)})

        parts.append({"text": "Now produce the summary in Markdown."})
        return [{"role": "user", "parts": parts}]
    
    def generate(self, snapshot: Dict) -> str:
        """
        Generate a summary from a session snapshot.
        """
        contents = self.build_prompt(snapshot)
        
        config = types.GenerateContentConfig(
            system_instruction="You are a study buddy enhancing note-taking layouts into smart formats.",
            temperature=0.3,
            max_output_tokens=2048,
        )
        
        resp = self.client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=contents,
            config=config,
        )
        
        return (getattr(resp, "text", "") or "").strip()
