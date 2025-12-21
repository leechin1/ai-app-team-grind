# AI Study App - Monorepo Guide

**Repository Structure:** Backend (FastAPI/Python) + Frontend (React/TypeScript/Vite)

---

## 📁 Repository Structure

```
ai-app-team-grind/
├── backend/                    # Python FastAPI Backend
│   ├── core/                   # Core modules
│   │   ├── models.py          # Pydantic models
│   │   ├── ai_generator.py    # Gemini AI integration
│   │   ├── spaced_repetition.py  # SM-2 algorithm
│   │   ├── review_logger.py   # Multi-source data logging
│   │   └── feature_extraction.py # ML features
│   ├── scripts/               # Test & utility scripts
│   ├── utils/                 # Helper utilities
│   ├── data/                  # Data storage
│   ├── main.py                # FastAPI application
│   ├── start_server.bat       # Quick start script
│   └── API_DOCUMENTATION.md   # API docs
│
├── frontend/                   # React TypeScript Frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/             # Page components
│   │   ├── lib/               # Utilities & API client
│   │   └── hooks/             # Custom React hooks
│   ├── public/                # Static assets
│   ├── package.json
│   └── vite.config.ts         # Vite configuration
│
├── docs/                       # Shared documentation
│   └── spaced_repetition_timeline.md
│
├── notiq_env/                  # Python virtual environment
├── .env                        # Environment variables
├── .gitignore                  # Git ignore rules
└── README.md                   # Project overview
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.11+** (for backend)
- **Node.js 18+** (for frontend)
- **Git** (for version control)

---

## 🔧 Backend Setup

### 1. Install Python Dependencies

```bash
# From project root
cd backend

# Activate virtual environment
..\notiq_env\Scripts\activate

# Install dependencies (if needed)
pip install -r requirements.txt
```

### 2. Configure Environment

Create/edit `.env` in project root:
```
GEMINI_API_KEY=your-api-key-here
```

### 3. Test Backend

```bash
# Test core functionality
python scripts/test_spaced_repetition.py
python scripts/test_ai_generator.py

# Check data analytics
python scripts/check_ml_readiness.py
```

### 4. Start Backend Server

```bash
# Option 1: Use batch file
start_server.bat

# Option 2: Direct command
python main.py
```

Server runs at: **http://localhost:8000**
API docs at: **http://localhost:8000/docs**

---

## 💻 Frontend Setup

### 1. Install Node Dependencies

```bash
# From project root
cd frontend

# Install dependencies
npm install
# or if using bun
bun install
```

### 2. Configure Frontend

The frontend expects the backend at `http://localhost:8000`.

Check `frontend/src/lib/api.ts` for API configuration:
```typescript
const api = axios.create({
  baseURL: 'http://localhost:8000',  // Backend URL
  headers: {
    'Content-Type': 'application/json'
  }
});
```

### 3. Start Frontend Dev Server

```bash
# From frontend/ directory
npm run dev
# or
bun run dev
```

Frontend runs at: **http://localhost:5173** (Vite) or **http://localhost:3000** (if configured)

---

## 🔄 Development Workflow

### Running Both Frontend & Backend

**Terminal 1 - Backend:**
```bash
cd backend
..\notiq_env\Scripts\activate
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Now you have:
- Backend API: http://localhost:8000
- Frontend App: http://localhost:5173
- API Docs: http://localhost:8000/docs

---

## 📡 API Integration

The frontend calls the backend API. Example:

```typescript
// frontend/src/lib/api.ts
import api from './api';

// Generate flashcards
const response = await api.post('/api/flashcards/generate', {
  content: text,
  num_flashcards: 10,
  difficulty: 'medium'
});

// Get due flashcards
const { data } = await api.get('/api/flashcards/due');

// Review flashcard
await api.post('/api/flashcards/review', {
  flashcard_id: id,
  response_quality: 5,
  was_correct: true,
  time_spent_seconds: 3.5
});
```

See [backend/API_DOCUMENTATION.md](backend/API_DOCUMENTATION.md) for complete API reference.

---

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Test AI generation
python scripts/test_ai_generator.py

# Test spaced repetition
python scripts/test_spaced_repetition.py

# Check ML readiness
python scripts/check_ml_readiness.py

# Analyze data
python scripts/analyze_review_data.py
```

### Frontend Tests

```bash
cd frontend

# Run tests (if configured)
npm test
```

---

## 📦 Building for Production

### Backend

```bash
cd backend

# Install production dependencies
pip install uvicorn gunicorn

# Run with Gunicorn (production server)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

### Frontend

```bash
cd frontend

# Build production bundle
npm run build

# Preview production build
npm run preview
```

Output will be in `frontend/dist/`

---

## 🔐 Environment Variables

### Backend (.env in project root)
```
GEMINI_API_KEY=your-gemini-api-key
```

### Frontend (frontend/.env.local)
```
VITE_API_URL=http://localhost:8000
```

---

## 📚 Documentation

- **API Documentation:** [backend/API_DOCUMENTATION.md](backend/API_DOCUMENTATION.md)
- **Testing Report:** [backend/TESTING_REPORT.md](backend/TESTING_REPORT.md)
- **SRS Timeline:** [docs/spaced_repetition_timeline.md](docs/spaced_repetition_timeline.md)
- **Main README:** [README.md](README.md)
- **Roadmap:** [Roadmap.md](Roadmap.md)

---

## 🐛 Troubleshooting

### Backend Issues

**ImportError: No module named 'fastapi'**
```bash
cd backend
pip install fastapi uvicorn
```

**API Key not configured**
```bash
# Check .env file exists in project root
cat .env  # Should show GEMINI_API_KEY=...
```

### Frontend Issues

**Module not found errors**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**CORS errors**
- Check backend CORS settings in `backend/main.py`
- Ensure frontend URL is in `allow_origins` list

---

## 🚢 Deployment

### Option 1: Separate Deployment

**Backend:**
- Deploy to Railway, Render, or Fly.io
- Set environment variables
- Use Gunicorn for production

**Frontend:**
- Deploy to Vercel, Netlify, or Cloudflare Pages
- Update API URL to production backend

### Option 2: Docker

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    depends_on:
      - backend
```

---

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes in `backend/` or `frontend/`
3. Test changes
4. Commit: `git commit -m "Add your feature"`
5. Push: `git push origin feature/your-feature`
6. Create Pull Request

---

## 📄 License

MIT License - See LICENSE file for details

---

## 👥 Team

- **Backend:** Python, FastAPI, SM-2, ML
- **Frontend:** React, TypeScript, Vite, TailwindCSS

---

## 🔗 Useful Links

- Backend API Docs: http://localhost:8000/docs
- Frontend Dev Server: http://localhost:5173
- Gemini API: https://ai.google.dev/

---

**Happy coding! 🚀**
