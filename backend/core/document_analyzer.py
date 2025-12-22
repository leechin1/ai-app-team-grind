"""
Document Analyzer and Router.

Analyzes raw text content and routes it to the appropriate template
(academic, scientific, or graphical) for structured processing.
"""

import re
from typing import Tuple, Dict, Any, Optional
from core.document_templates import (
    TemplateType, AcademicTemplate, ScientificTemplate, GraphicalTemplate,
    AcademicSection, AcademicReference, Hypothesis, Methodology, Finding,
    VisualElement, Slide
)
import google.generativeai as genai
import os
import json


class DocumentAnalyzer:
    """Analyzes documents and routes them to appropriate templates"""

    def __init__(self, gemini_api_key: Optional[str] = None):
        """Initialize the analyzer with Gemini API key"""
        self.api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            # Use gemini-pro for v1 API compatibility
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None

    def analyze_document_type(self, content: str) -> Tuple[TemplateType, float]:
        """
        Analyze content and determine the best template type.

        Returns:
            Tuple of (template_type, confidence_score)
        """
        content_lower = content.lower()

        # Scoring for each template type
        scores = {
            TemplateType.ACADEMIC: 0.0,
            TemplateType.SCIENTIFIC: 0.0,
            TemplateType.GRAPHICAL: 0.0
        }

        # Academic indicators
        academic_keywords = [
            'essay', 'thesis', 'argument', 'introduction', 'conclusion',
            'paragraph', 'analysis', 'discuss', 'compare', 'contrast',
            'references', 'bibliography', 'citation', 'abstract'
        ]
        scores[TemplateType.ACADEMIC] = sum(
            content_lower.count(kw) for kw in academic_keywords
        )

        # Scientific indicators
        scientific_keywords = [
            'hypothesis', 'experiment', 'methodology', 'results', 'data',
            'findings', 'research', 'study', 'analysis', 'statistical',
            'method', 'procedure', 'materials', 'discussion', 'literature review'
        ]
        scores[TemplateType.SCIENTIFIC] = sum(
            content_lower.count(kw) for kw in scientific_keywords
        )

        # Graphical/Visual indicators
        graphical_keywords = [
            'slide', 'presentation', 'infographic', 'chart', 'graph',
            'diagram', 'visual', 'figure', 'image', 'illustration',
            'page', 'section', 'overview', 'key points'
        ]
        scores[TemplateType.GRAPHICAL] = sum(
            content_lower.count(kw) for kw in graphical_keywords
        )

        # Check for numbered pages (common in presentations)
        if re.search(r'(page|slide)\s+\d+', content_lower):
            scores[TemplateType.GRAPHICAL] += 10

        # Check for hypothesis format (scientific)
        if re.search(r'(h0|h1|null hypothesis|alternative hypothesis)', content_lower):
            scores[TemplateType.SCIENTIFIC] += 15

        # Check for thesis statement (academic)
        if re.search(r'thesis statement', content_lower):
            scores[TemplateType.ACADEMIC] += 10

        # Determine best template
        max_score = max(scores.values())
        if max_score == 0:
            # Default to academic if no clear indicators
            return TemplateType.ACADEMIC, 0.5

        best_template = max(scores, key=scores.get)
        confidence = min(max_score / (sum(scores.values()) or 1), 1.0)

        return best_template, confidence

    async def process_with_ai(self, content: str, template_type: TemplateType) -> Dict[str, Any]:
        """
        Use Gemini AI to extract structured information from the content.

        Returns:
            Dictionary with extracted structured data
        """
        if not self.model:
            raise ValueError("Gemini API key not configured")

        # Create prompts based on template type
        if template_type == TemplateType.ACADEMIC:
            prompt = self._get_academic_extraction_prompt(content)
        elif template_type == TemplateType.SCIENTIFIC:
            prompt = self._get_scientific_extraction_prompt(content)
        else:  # GRAPHICAL
            prompt = self._get_graphical_extraction_prompt(content)

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text

            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(1)

            return json.loads(result_text)

        except Exception as e:
            print(f"AI processing error: {e}")
            # Return basic structure as fallback
            return self._create_fallback_structure(content, template_type)

    def _get_academic_extraction_prompt(self, content: str) -> str:
        """Generate prompt for academic document extraction"""
        # Use full content, Gemini can handle larger inputs
        return f"""
Analyze the following academic text and extract structured information in JSON format.

IMPORTANT: Process the ENTIRE document, not just the first page. Extract ALL sections, subsections, and content.

Text:
{content}

Extract the following information from the COMPLETE document:
1. Title of the document
2. Author (if mentioned)
3. Main thesis or argument
4. Introduction content (complete, not summary)
5. ALL main sections with their titles and FULL content (not summaries)
6. Conclusion content (complete, not summary)
7. Key keywords and concepts (at least 5)
8. Any references or citations found throughout the document

DO NOT summarize - extract the actual content from each section.
If a section is long, include the full text, not a shortened version.

Return ONLY a valid JSON object with this structure:
{{
    "title": "string",
    "author": "string or null",
    "thesis_statement": "string or null",
    "introduction": "string",
    "sections": [
        {{
            "title": "string",
            "content": "string",
            "key_points": ["string"]
        }}
    ],
    "conclusion": "string",
    "keywords": ["string"],
    "abstract": "string or null"
}}
"""

    def _get_scientific_extraction_prompt(self, content: str) -> str:
        """Generate prompt for scientific document extraction"""
        return f"""
Analyze the following scientific text and extract structured information in JSON format.

IMPORTANT: Process the ENTIRE document, not just the first page. Extract ALL sections and content completely.

Text:
{content}

Extract the following information from the COMPLETE document:
1. Research title
2. Authors and institution
3. Abstract (complete text)
4. Introduction/background (complete section, not summary)
5. Hypothesis (if present)
6. Methodology details (complete, including all steps and procedures)
7. Results and findings (all results, not just first page)
8. Discussion (complete analysis)
9. Conclusion (full conclusion)
10. Keywords

DO NOT summarize - extract the actual complete content from each section.
Process all pages, not just page 1.

Return ONLY a valid JSON object with this structure:
{{
    "title": "string",
    "authors": ["string"],
    "institution": "string or null",
    "abstract": "string",
    "introduction": "string",
    "hypothesis": {{
        "statement": "string",
        "variables": ["string"],
        "prediction": "string or null"
    }},
    "methodology": {{
        "approach": "string",
        "steps": ["string"],
        "materials": ["string"]
    }},
    "results": [
        {{
            "description": "string",
            "data": "string or null"
        }}
    ],
    "discussion": "string",
    "conclusion": "string",
    "keywords": ["string"]
}}
"""

    def _get_graphical_extraction_prompt(self, content: str) -> str:
        """Generate prompt for graphical/presentation document extraction"""
        return f"""
Analyze the following presentation/visual document and extract structured information in JSON format.

IMPORTANT: Process the ENTIRE document, not just the first page. Extract ALL slides/sections and content.

Text:
{content}

Extract the following information from the COMPLETE document:
1. Main title and subtitle
2. Overview/executive summary
3. ALL individual slides/sections with their COMPLETE content (not summaries)
4. Visual elements mentioned (charts, diagrams, images)
5. Key messages or takeaways
6. Any call to action

DO NOT summarize - extract full content from all slides/sections.
Process all pages, not just the first one.

Return ONLY a valid JSON object with this structure:
{{
    "title": "string",
    "subtitle": "string or null",
    "overview": "string",
    "slides": [
        {{
            "title": "string",
            "content": "string",
            "visuals": [
                {{
                    "type": "string",
                    "title": "string",
                    "description": "string",
                    "key_insights": ["string"]
                }}
            ]
        }}
    ],
    "key_messages": ["string"],
    "call_to_action": "string or null"
}}
"""

    def _create_fallback_structure(self, content: str, template_type: TemplateType) -> Dict[str, Any]:
        """Create basic structure when AI processing fails"""
        lines = content.split('\n')
        title = lines[0][:100] if lines else "Untitled Document"

        if template_type == TemplateType.ACADEMIC:
            return {
                "title": title,
                "introduction": content[:500],
                "sections": [{"title": "Content", "content": content, "key_points": []}],
                "conclusion": "See document for full details.",
                "keywords": []
            }
        elif template_type == TemplateType.SCIENTIFIC:
            return {
                "title": title,
                "abstract": content[:300],
                "introduction": content[:500],
                "methodology": {"approach": "See document", "steps": [], "materials": []},
                "results": [{"description": "See document", "data": None}],
                "discussion": "See document for full analysis.",
                "conclusion": "See document for conclusions.",
                "keywords": []
            }
        else:  # GRAPHICAL
            return {
                "title": title,
                "overview": content[:300],
                "slides": [{"title": "Content", "content": content, "visuals": []}],
                "key_messages": []
            }

    async def process_document(self, content: str) -> Tuple[str, str]:
        """
        Process a document end-to-end.

        Args:
            content: Raw document text

        Returns:
            Tuple of (formatted_markdown, template_type_used)
        """
        # Step 1: Analyze and determine template type
        template_type, confidence = self.analyze_document_type(content)
        print(f"Detected template: {template_type.value} (confidence: {confidence:.2f})")

        # Step 2: Extract structured information using AI
        try:
            structured_data = await self.process_with_ai(content, template_type)
        except Exception as e:
            print(f"AI extraction failed, using fallback: {e}")
            structured_data = self._create_fallback_structure(content, template_type)

        # Step 3: Create appropriate template instance
        if template_type == TemplateType.ACADEMIC:
            template = AcademicTemplate(**structured_data)
        elif template_type == TemplateType.SCIENTIFIC:
            template = ScientificTemplate(**structured_data)
        else:  # GRAPHICAL
            template = GraphicalTemplate(**structured_data)

        # Step 4: Convert to markdown
        markdown_output = template.to_markdown()

        return markdown_output, template_type.value


# Synchronous wrapper for easy use
def process_document_sync(content: str, gemini_api_key: Optional[str] = None) -> Tuple[str, str]:
    """
    Synchronous version of document processing.

    Args:
        content: Raw document text
        gemini_api_key: Optional API key (uses env variable if not provided)

    Returns:
        Tuple of (formatted_markdown, template_type_used)
    """
    import asyncio

    analyzer = DocumentAnalyzer(gemini_api_key)
    return asyncio.run(analyzer.process_document(content))
