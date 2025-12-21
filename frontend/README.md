# Notiq

Notiq is an intelligent platform for structuring notes and chatting with your documents, powered by Google Gemini.

## Technical Architecture

The architecture is designed for scalability and performance, separating the client and server concerns while maintaining type safety and ease of deployment.

### 1. Frontend (Client-Side)
- **Framework**: [React 18](https://react.dev/) using [Vite](https://vitejs.dev/) for high-performance tooling.
- **Language**: TypeScript for type safety and developer experience.
- **Styling**: [Tailwind CSS](https://tailwindcss.com/) combined with [Shadcn UI](https://ui.shadcn.com/) for a modern, accessible, and responsive design system.
- **State Management**: [TanStack Query](https://tanstack.com/query/latest) handles server state, caching, and synchronization.
- **Routing**: `react-router-dom` manage client-side navigation.

### 2. Backend (Server-Side)
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/), a modern, high-performance web framework for building APIs with Python 3.8+.
- **AI Engine**: Direct integration with **Google Gemini (GenAI)** for logic-heavy tasks like note structuring and context-aware chat.
- **Data & Storage**: **Supabase** is utilized for database needs and object storage (e.g., file uploads).
- **API Design**: Adheres to RESTful principles.

### 3. Infrastructure
- **Monorepo**: The codebase houses both `frontend` and `api` directories, simplifying development and dependency management.
- **Deployment**: The project is configured for [Vercel](https://vercel.com/) via `vercel.json`, supporting both the static frontend and serverless Python functions.

## Getting Started

### Prerequisites
- Node.js & npm
- Python 3.10+
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/IshakSoltani/Notiq.git
   cd Notiq
   ```

2. Setup Backend:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Mac/Linux
   # source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Setup Frontend:
   ```bash
   cd frontend
   npm install
   ```

4. Environment Variables:
   - Create a `.env` file in the root based on your configuration (API keys for Gemini, Supabase, etc).

### Running Locally

- **Backend**:
  ```bash
  python -m uvicorn api.index:app --reload
  ```

- **Frontend**:
  ```bash
  cd frontend
  npm run dev
  ```
