"""
Document Processing Templates using Pydantic Models.

Three smart templates for different document types:
1. Academic - For essays, reports, academic papers
2. Scientific - For research papers, lab reports, technical documents
3. Graphical - For visual content, presentations, infographics
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum


class TemplateType(str, Enum):
    """Types of document templates"""
    ACADEMIC = "academic"
    SCIENTIFIC = "scientific"
    GRAPHICAL = "graphical"


# ==================== ACADEMIC TEMPLATE ====================

class AcademicSection(BaseModel):
    """A section in an academic document"""
    title: str = Field(..., description="Section heading")
    content: str = Field(..., description="Section content")
    subsections: Optional[List['AcademicSection']] = Field(default=None, description="Nested subsections")
    key_points: List[str] = Field(default_factory=list, description="Key points from this section")


class AcademicReference(BaseModel):
    """A bibliographic reference"""
    authors: List[str] = Field(default_factory=list)
    title: str
    year: Optional[int] = None
    publication: Optional[str] = None
    citation_key: Optional[str] = None


class AcademicTemplate(BaseModel):
    """
    Template for academic documents (essays, reports, papers).

    Focuses on: structure, argumentation, citations, and formal writing.
    """
    template_type: TemplateType = Field(default=TemplateType.ACADEMIC)

    # Document metadata
    title: str = Field(..., description="Document title")
    author: Optional[str] = Field(None, description="Document author")
    date: Optional[str] = Field(None, description="Document date")
    abstract: Optional[str] = Field(None, description="Abstract or summary")

    # Document structure
    introduction: Optional[str] = Field(None, description="Introduction section")
    sections: List[AcademicSection] = Field(default_factory=list, description="Main body sections")
    conclusion: Optional[str] = Field(None, description="Conclusion section")

    # Academic elements
    thesis_statement: Optional[str] = Field(None, description="Main thesis/argument")
    references: List[AcademicReference] = Field(default_factory=list, description="Bibliography")
    keywords: List[str] = Field(default_factory=list, description="Key terms and concepts")

    def to_markdown(self) -> str:
        """Convert to formatted markdown"""
        md = f"# {self.title}\n\n"

        if self.author:
            md += f"**Author:** {self.author}\n\n"
        if self.date:
            md += f"**Date:** {self.date}\n\n"

        if self.abstract:
            md += f"## Abstract\n\n{self.abstract}\n\n"

        if self.thesis_statement:
            md += f"## Thesis Statement\n\n{self.thesis_statement}\n\n"

        if self.introduction:
            md += f"## Introduction\n\n{self.introduction}\n\n"

        # Add main sections
        for section in self.sections:
            md += self._section_to_markdown(section, level=2)

        if self.conclusion:
            md += f"## Conclusion\n\n{self.conclusion}\n\n"

        # Add keywords
        if self.keywords:
            md += "## Keywords\n\n"
            md += ", ".join(f"*{kw}*" for kw in self.keywords) + "\n\n"

        # Add references
        if self.references:
            md += "## References\n\n"
            for ref in self.references:
                authors = ", ".join(ref.authors) if ref.authors else "Unknown"
                year = f" ({ref.year})" if ref.year else ""
                pub = f" *{ref.publication}*" if ref.publication else ""
                md += f"- {authors}{year}. {ref.title}.{pub}\n"

        return md

    def _section_to_markdown(self, section: AcademicSection, level: int = 2) -> str:
        """Convert a section to markdown recursively"""
        md = f"{'#' * level} {section.title}\n\n"
        md += f"{section.content}\n\n"

        if section.key_points:
            md += "**Key Points:**\n"
            for point in section.key_points:
                md += f"- {point}\n"
            md += "\n"

        if section.subsections:
            for subsection in section.subsections:
                md += self._section_to_markdown(subsection, level + 1)

        return md


# ==================== SCIENTIFIC TEMPLATE ====================

class Hypothesis(BaseModel):
    """A scientific hypothesis"""
    statement: str = Field(..., description="Hypothesis statement")
    variables: List[str] = Field(default_factory=list, description="Variables involved")
    prediction: Optional[str] = Field(None, description="Expected outcome")


class Methodology(BaseModel):
    """Research methodology description"""
    approach: str = Field(..., description="Overall methodology approach")
    steps: List[str] = Field(default_factory=list, description="Step-by-step procedure")
    materials: List[str] = Field(default_factory=list, description="Materials/equipment used")
    data_collection: Optional[str] = Field(None, description="Data collection methods")


class Finding(BaseModel):
    """A research finding or result"""
    description: str = Field(..., description="Finding description")
    data: Optional[str] = Field(None, description="Supporting data/evidence")
    significance: Optional[str] = Field(None, description="Statistical significance or importance")


class ScientificTemplate(BaseModel):
    """
    Template for scientific documents (research papers, lab reports).

    Focuses on: hypothesis, methodology, results, data, and scientific rigor.
    """
    template_type: TemplateType = Field(default=TemplateType.SCIENTIFIC)

    # Document metadata
    title: str = Field(..., description="Research title")
    authors: List[str] = Field(default_factory=list, description="Research authors")
    institution: Optional[str] = Field(None, description="Research institution")
    date: Optional[str] = Field(None, description="Publication/submission date")

    # Scientific structure
    abstract: Optional[str] = Field(None, description="Research abstract")
    introduction: Optional[str] = Field(None, description="Background and context")
    literature_review: Optional[str] = Field(None, description="Related work review")

    hypothesis: Optional[Hypothesis] = Field(None, description="Research hypothesis")
    methodology: Optional[Methodology] = Field(None, description="Research methods")

    results: List[Finding] = Field(default_factory=list, description="Research findings")
    discussion: Optional[str] = Field(None, description="Interpretation of results")
    conclusion: Optional[str] = Field(None, description="Conclusions and implications")

    # Scientific elements
    keywords: List[str] = Field(default_factory=list, description="Scientific keywords")
    figures: List[Dict[str, str]] = Field(default_factory=list, description="Figure references")
    tables: List[Dict[str, str]] = Field(default_factory=list, description="Table references")
    limitations: List[str] = Field(default_factory=list, description="Study limitations")
    future_work: List[str] = Field(default_factory=list, description="Future research directions")

    def to_markdown(self) -> str:
        """Convert to formatted markdown"""
        md = f"# {self.title}\n\n"

        if self.authors:
            md += f"**Authors:** {', '.join(self.authors)}\n\n"
        if self.institution:
            md += f"**Institution:** {self.institution}\n\n"
        if self.date:
            md += f"**Date:** {self.date}\n\n"

        if self.abstract:
            md += f"## Abstract\n\n{self.abstract}\n\n"

        if self.keywords:
            md += f"**Keywords:** {', '.join(self.keywords)}\n\n"

        if self.introduction:
            md += f"## Introduction\n\n{self.introduction}\n\n"

        if self.literature_review:
            md += f"## Literature Review\n\n{self.literature_review}\n\n"

        if self.hypothesis:
            md += f"## Hypothesis\n\n"
            md += f"{self.hypothesis.statement}\n\n"
            if self.hypothesis.variables:
                md += f"**Variables:** {', '.join(self.hypothesis.variables)}\n\n"
            if self.hypothesis.prediction:
                md += f"**Prediction:** {self.hypothesis.prediction}\n\n"

        if self.methodology:
            md += f"## Methodology\n\n"
            md += f"{self.methodology.approach}\n\n"
            if self.methodology.steps:
                md += "**Procedure:**\n"
                for i, step in enumerate(self.methodology.steps, 1):
                    md += f"{i}. {step}\n"
                md += "\n"
            if self.methodology.materials:
                md += f"**Materials:** {', '.join(self.methodology.materials)}\n\n"

        md += f"## Results\n\n"
        for i, finding in enumerate(self.results, 1):
            md += f"### Finding {i}\n\n"
            md += f"{finding.description}\n\n"
            if finding.data:
                md += f"**Data:** {finding.data}\n\n"
            if finding.significance:
                md += f"**Significance:** {finding.significance}\n\n"

        if self.discussion:
            md += f"## Discussion\n\n{self.discussion}\n\n"

        if self.limitations:
            md += "### Limitations\n\n"
            for limitation in self.limitations:
                md += f"- {limitation}\n"
            md += "\n"

        if self.conclusion:
            md += f"## Conclusion\n\n{self.conclusion}\n\n"

        if self.future_work:
            md += "### Future Research Directions\n\n"
            for work in self.future_work:
                md += f"- {work}\n"
            md += "\n"

        return md


# ==================== GRAPHICAL TEMPLATE ====================

class VisualElement(BaseModel):
    """A visual element in the document"""
    type: str = Field(..., description="Type of visual (image, chart, diagram, etc.)")
    title: str = Field(..., description="Visual element title")
    description: str = Field(..., description="Description of the visual")
    key_insights: List[str] = Field(default_factory=list, description="Insights from the visual")
    data_points: Optional[List[str]] = Field(default=None, description="Key data points shown")


class Slide(BaseModel):
    """A presentation slide or section"""
    title: str = Field(..., description="Slide title")
    content: Optional[str] = Field(None, description="Slide content")
    visuals: List[VisualElement] = Field(default_factory=list, description="Visual elements")
    notes: Optional[str] = Field(None, description="Speaker notes or additional context")


class GraphicalTemplate(BaseModel):
    """
    Template for visual/graphical documents (presentations, infographics, visual reports).

    Focuses on: visual hierarchy, key messages, data visualization, and design elements.
    """
    template_type: TemplateType = Field(default=TemplateType.GRAPHICAL)

    # Document metadata
    title: str = Field(..., description="Presentation/document title")
    subtitle: Optional[str] = Field(None, description="Subtitle or tagline")
    author: Optional[str] = Field(None, description="Creator")
    date: Optional[str] = Field(None, description="Creation date")

    # Visual structure
    overview: Optional[str] = Field(None, description="Executive summary or overview")
    slides: List[Slide] = Field(default_factory=list, description="Main slides/sections")

    # Graphical elements
    key_messages: List[str] = Field(default_factory=list, description="Main takeaways")
    color_scheme: Optional[str] = Field(None, description="Color palette description")
    design_notes: Optional[str] = Field(None, description="Design considerations")
    call_to_action: Optional[str] = Field(None, description="Final call to action")

    def to_markdown(self) -> str:
        """Convert to formatted markdown with visual emphasis"""
        md = f"# {self.title}\n\n"

        if self.subtitle:
            md += f"### {self.subtitle}\n\n"

        if self.author:
            md += f"**Created by:** {self.author}\n\n"
        if self.date:
            md += f"**Date:** {self.date}\n\n"

        md += "---\n\n"

        if self.overview:
            md += f"## Overview\n\n{self.overview}\n\n"

        if self.key_messages:
            md += "## 🎯 Key Messages\n\n"
            for msg in self.key_messages:
                md += f"- **{msg}**\n"
            md += "\n---\n\n"

        # Add slides
        for i, slide in enumerate(self.slides, 1):
            md += f"## Slide {i}: {slide.title}\n\n"
            if slide.content:
                md += f"{slide.content}\n\n"

            if slide.visuals:
                md += "### 📊 Visual Elements\n\n"
                for visual in slide.visuals:
                    md += f"#### {visual.type.title()}: {visual.title}\n\n"
                    md += f"{visual.description}\n\n"
                    if visual.key_insights:
                        md += "**Key Insights:**\n"
                        for insight in visual.key_insights:
                            md += f"- {insight}\n"
                        md += "\n"

            if slide.notes:
                md += f"> 📝 **Notes:** {slide.notes}\n\n"

            md += "---\n\n"

        if self.call_to_action:
            md += f"## 🚀 Next Steps\n\n{self.call_to_action}\n\n"

        return md


# Allow forward references for recursive models
AcademicSection.model_rebuild()
