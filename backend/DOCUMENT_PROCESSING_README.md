# Document Processing System

This system automatically analyzes, routes, and formats documents using AI-powered smart templates.

## Overview

When a user uploads a PDF or writes content in the markdown editor, the system:

1. **Analyzes** the document to determine its type
2. **Routes** it to the most appropriate template
3. **Processes** it with AI to extract structured information
4. **Formats** it as beautiful markdown output

## Components

### 1. Template Models (`backend/core/document_templates.py`)

Three Pydantic-based smart templates:

#### **Academic Template**
- For essays, reports, academic papers
- Extracts: thesis statement, sections, conclusion, references
- Focuses on argumentation and formal structure

#### **Scientific Template**
- For research papers, lab reports, technical documents
- Extracts: hypothesis, methodology, results, discussion
- Focuses on scientific rigor and data presentation

#### **Graphical Template**
- For presentations, infographics, visual reports
- Extracts: slides, visual elements, key messages
- Focuses on visual hierarchy and design elements

### 2. Document Analyzer (`backend/core/document_analyzer.py`)

**Key Functions:**

- `analyze_document_type(content)`: Determines the best template using keyword analysis
- `process_with_ai(content, template_type)`: Uses Gemini AI to extract structured data
- `process_document(content)`: End-to-end processing pipeline

**How It Works:**

1. Scans content for template-specific keywords
2. Scores each template type based on indicators
3. Selects the best match with confidence score
4. Uses Gemini AI to intelligently extract structured information
5. Creates appropriate template instance
6. Converts to formatted markdown

### 3. API Endpoint (`backend/main.py`)

**Endpoint:** `POST /api/documents/process`

**Request:**
```json
{
  "content": "raw document text...",
  "document_id": "optional-id"
}
```

**Response:**
```json
{
  "formatted_content": "# Beautiful Markdown...",
  "template_type": "academic",
  "document_id": "doc-123"
}
```

### 4. Frontend Integration (`frontend/src/lib/api.ts` & `Dashboard.tsx`)

When the user creates a note:

1. Content is sent to `/api/documents/process`
2. Backend analyzes and formats the document
3. Formatted markdown is displayed in the Studio panel
4. User sees which template was used (academic, scientific, or graphical)

## Usage Example

### Input (Raw Text):
```
Research on Machine Learning

Introduction
This study examines...

Methodology
We used a dataset of 10,000 samples...

Results
Our model achieved 95% accuracy...
```

### Output (Formatted):
```markdown
# Research on Machine Learning

**Authors:** Research Team

## Abstract
[AI-generated summary]

## Introduction
This study examines...

## Methodology
**Approach:** Experimental study
**Steps:**
1. Data collection
2. Model training
3. Evaluation

## Results
### Finding 1
Our model achieved 95% accuracy...

## Discussion
[AI-generated analysis]

## Conclusion
[AI-generated conclusion]
```

## Template Selection Logic

The analyzer uses keyword frequency and pattern matching:

### Academic Indicators:
- essay, thesis, argument, introduction, conclusion
- references, bibliography, citation

### Scientific Indicators:
- hypothesis, experiment, methodology, results
- research, study, data, statistical

### Graphical Indicators:
- slide, presentation, chart, graph, diagram
- visual, figure, infographic

## AI Processing

Uses Google Gemini 1.5 Flash to:

1. Extract document structure
2. Identify key sections
3. Generate missing elements (abstract, keywords, etc.)
4. Organize content hierarchically
5. Format citations and references

## Error Handling

- Falls back to basic structure if AI processing fails
- Defaults to Academic template if no clear indicators
- Handles missing API keys gracefully

## Future Enhancements

- [ ] Custom template creation
- [ ] Template preview before processing
- [ ] Multi-language support
- [ ] Export to different formats (PDF, DOCX)
- [ ] Version history for processed documents
- [ ] Collaborative editing
