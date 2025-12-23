# Notiq UI Redesign - Notion/Obsidian Style

## 🎯 Objetivo
Transformar Notiq numa aplicação estilo Notion/Obsidian com editor de texto principal, projetos, e AI integrada.

## 📐 Nova Estrutura

### 1. Authentication (Landing)
- **Route**: `/` (Index)
- **Features**:
  - Logo + Hero section
  - "Login" button (fake auth for MVP)
  - "Continue as Guest" button
  - Clean, modern design

**MVP Auth**:
```typescript
// Fake user for MVP
const FAKE_USER = {
  id: "user-123",
  email: "demo@notiq.app",
  name: "Demo User"
}
```

---

### 2. Main Layout (After Login)
- **Route**: `/home` or `/projects/:projectId`
- **Layout**:
  ```
  ┌─────────┬───────────────────────────────┐
  │         │                               │
  │ Sidebar │   Editor (40-50% width)       │
  │  (20%)  │   + Blank space (blend)       │
  │         │                               │
  └─────────┴───────────────────────────────┘
  ```

**Sidebar Buttons**:
1. 🏠 **Home** - Projects list
2. 💬 **ChatIQ** - AI Chatbot (project-scoped)
3. 🧠 **Flashcards** - Study with flashcards
4. ⚡ **Match Quiz** - Match fronts/backs
5. 🎯 **Quiz** - Multiple choice
6. 📁 **Files** - Upload documents

---

### 3. Home Page (Projects List)
- **Route**: `/home`
- **UI**:
  ```
  Big Title: "Projects"
  ┌──────────────┐  ┌──────────────┐
  │  📚 Biology  │  │ 💻 Programming│
  │  5 notes     │  │ 12 notes      │
  └──────────────┘  └──────────────┘

  + New Project button
  ```

- **Features**:
  - Grid of project cards
  - Each shows: icon, name, note count
  - Click → opens that project's editor

---

### 4. Project Editor
- **Route**: `/projects/:projectId`
- **UI**: Full Notion-style editor
  - Title input (large, bold)
  - Rich text editor (TipTap or similar)
  - Takes 40-50% center of screen
  - Rest of screen: blank with subtle gradient

**Features**:
- Auto-save
- Markdown support
- Slash commands (future)
- Full-screen focus mode

---

### 5. Files Page
- **Route**: `/files`
- **UI**: Upload interface
  - Drag & drop area
  - List of uploaded files per project
  - Filter by project

**Purpose**:
- Upload PDFs/docs for ChatIQ context
- Upload files for flashcard/quiz generation
- Files are scoped to current project

---

### 6. ChatIQ (AI Chatbot)
- **Route**: `/chatiq`
- **UI**: Chat interface (like ChatGPT)
  - Message history
  - Input box at bottom
  - Context indicator (shows what files/notes are in context)

**Context** (Project-Scoped):
- Current project's editor text
- Files uploaded to current project
- Embeddings from project notes (future RAG)

**Foundation for RAG**:
```python
# Backend structure
class ProjectContext:
    project_id: str
    editor_content: str  # Current note
    uploaded_files: List[File]
    embeddings: List[Embedding]  # Future: vector search
```

---

### 7. Flashcards/Quiz/Match
- **Route**: `/flashcards`, `/quiz`, `/match`
- **Changes**:
  - Scoped to current project
  - Generate from:
    - Project editor content
    - Project uploaded files
  - Review history per project

---

## 🗂️ New Data Models

### Project
```python
class Project(BaseModel):
    id: str
    user_id: str
    name: str
    icon: str  # emoji
    color: str  # for UI
    created_at: datetime
    updated_at: datetime
```

### Note (Editor Content)
```python
class Note(BaseModel):
    id: str
    project_id: str
    title: str
    content: str  # Rich text/Markdown
    created_at: datetime
    updated_at: datetime
```

### File (Uploaded Documents)
```python
class File(BaseModel):
    id: str
    project_id: str  # Scoped to project!
    filename: str
    content: str
    file_type: str
    uploaded_at: datetime
```

### ChatMessage
```python
class ChatMessage(BaseModel):
    id: str
    project_id: str  # Scoped to project!
    role: str  # "user" or "assistant"
    content: str
    context_used: List[str]  # IDs of files/notes used
    created_at: datetime
```

---

## 🎨 UI Components to Create

### Components
1. **Sidebar.tsx** - Left navigation
2. **ProjectCard.tsx** - Project grid item
3. **RichEditor.tsx** - Notion-style editor (TipTap)
4. **ChatInterface.tsx** - Chat UI
5. **FileUploader.tsx** - Upload interface
6. **ContextIndicator.tsx** - Shows active context

### Pages to Create
1. **Login.tsx** - Landing/auth
2. **Projects.tsx** - Projects list (Home)
3. **Editor.tsx** - Main note editor
4. **ChatIQ.tsx** - Chatbot interface
5. **Files.tsx** - File management

### Pages to Remove
- ❌ `Dashboard.tsx` (old)
- ❌ `Index.tsx` (will be replaced by Login)
- ❌ `StudyHub.tsx` (replaced by sidebar)

---

## 📦 Implementation Order

### Phase 1: Foundation (This session)
1. ✅ Create fake auth system
2. ✅ Create sidebar component
3. ✅ Create projects page
4. ✅ Update routing
5. ✅ Create basic editor page

### Phase 2: Backend Models
6. Add Project model to backend
7. Add Note model
8. Update File model (add project_id)
9. Add ChatMessage model
10. Create endpoints for projects CRUD

### Phase 3: Editor & Chat
11. Integrate TipTap editor
12. Build ChatIQ interface
13. Connect Gemini with project context
14. Implement auto-save

### Phase 4: Context & RAG
15. Build context aggregation system
16. Prepare for embeddings (structure only)
17. Update flashcards/quiz to use project scope

---

## 🚀 Let's Start!

Ready to begin Phase 1?
