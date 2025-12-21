# Notiq - AI-Powered Study Platform

An intelligent study platform that uses AI to generate flashcards, quizzes, and match games from your study materials. Features spaced repetition learning with the SM-2 algorithm.

## 🎯 Features

- **📄 Document Upload**: Upload PDFs and text files for automatic content extraction
- **🧠 AI Flashcards**: Generate flashcards with SM-2 spaced repetition algorithm
- **🎯 Interactive Quizzes**: Create and take multiple choice quizzes
- **⚡ Match Games**: Match terms with definitions in an interactive game
- **📊 Progress Tracking**: Track your learning progress and accuracy
- **🤖 ML Ready**: Automatic data collection for future ML model training

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** - [Download here](https://www.python.org/downloads/)
- **Node.js 18+** & **npm** - [Download here](https://nodejs.org/)
- **Gemini API Key** - [Get it here](https://makersuite.google.com/app/apikey)

### Installation Steps

#### 1. Clone the Repository

```bash
git clone https://github.com/your-repo/ai-app-team-grind.git
cd ai-app-team-grind
```

#### 2. Set Up Backend

```bash
# Create Python virtual environment
python -m venv notiq_env

# Activate virtual environment
# On Windows:
notiq_env\Scripts\activate

# Install backend dependencies
pip install -r backend/requirements.txt
```

#### 3. Configure API Key

Create a `.env` file in the project root:

```bash
# Windows PowerShell:
echo "GEMINI_API_KEY=your_api_key_here" | Out-File -FilePath .env -Encoding UTF8

# Or just create .env file manually and add:
GEMINI_API_KEY=your_api_key_here
```

Replace `your_api_key_here` with your actual Gemini API key.

#### 4. Set Up Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Go back to root
cd ..
```

### Running the Application

You need **TWO terminals** running simultaneously:

#### Terminal 1: Backend Server

```bash
# Activate virtual environment
notiq_env\Scripts\activate

# Run backend
cd backend
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Backend is now running at http://localhost:8000** ✅

#### Terminal 2: Frontend Server

Open a **NEW terminal** and run:

```bash
# Navigate to frontend directory
cd frontend

# Start development server
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in XXX ms

  ➜  Local:   http://localhost:5173/
```

**Frontend is now running at http://localhost:5173** ✅

### Access the App

Open your browser and go to:
```
http://localhost:5173
```

Click **"Study Hub"** to start using the app!

---

## 📖 How to Use

### 1. Upload Study Materials

1. Click **"Study Hub"** in the header
2. Go to **"Upload Material"**
3. Drag & drop or click to upload PDF/TXT files
4. Choose what to create: **Flashcards**, **Quiz**, or **Match Game**

### 2. Generate Flashcards

**Option A: From Uploaded Document**
1. Upload a document
2. In the success dialog, click **"Generate Flashcards"**
3. Adjust settings (number of cards, difficulty)
4. Click **"Generate Flashcards"**

**Option B: Manual Text**
1. Go to **Flashcards** page
2. Click **"Generate Cards"**
3. Paste your study material
4. Configure settings
5. Click **"Generate Flashcards"**

### 3. Review with Spaced Repetition

1. Go to **Flashcards** → **"Review Cards"**
2. Click cards to flip them (watch the smooth 3D animation!)
3. Rate your knowledge:
   - **Didn't Know** (Review soon)
   - **Somewhat** (Review in few days)
   - **Knew It** (Review in a week)
   - **Easy!** (Review much later)

The SM-2 algorithm automatically schedules reviews!

### 4. Take Quizzes

1. Go to **Quiz** page
2. Generate from uploaded document or paste text
3. Take the quiz
4. Submit to see results and detailed explanations

### 5. Play Match Games

1. Go to **Match Quiz** page
2. Generate pairs from your material
3. Click a term, then its matching definition
4. Complete all matches to see your score!

---

## 🛠️ Troubleshooting

### Backend won't start?

**Check 1: Virtual environment**
```bash
# Activate it first
notiq_env\Scripts\activate
```

**Check 2: API key**
```bash
# Verify .env file exists in project root
type .env
# Should show: GEMINI_API_KEY=...
```

**Check 3: Dependencies**
```bash
pip install -r backend/requirements.txt
```

### Frontend won't start?

**Check 1: Node modules**
```bash
cd frontend
npm install
```

**Check 2: Port already in use**
```bash
# Kill process on port 5173 (Windows)
netstat -ano | findstr :5173
taskkill /PID <PID> /F
```

### "npm: command not found"

**Windows:**
1. Install Node.js from https://nodejs.org/
2. Restart your terminal
3. Verify: `npm --version`

### API calls failing?

**Check 1: Backend is running**
Open browser: http://localhost:8000/health
Should return: `{"status":"healthy",...}`

**Check 2: CORS errors**
- Make sure both servers are running
- Backend should show CORS middleware loaded

**Check 3: API key**
- Visit http://localhost:8000/docs
- Try the `/health` endpoint
- Check if `api_key_configured` is `true`

---

## 📁 Project Structure

```
ai-app-team-grind/
├── backend/                 # Python FastAPI backend
│   ├── core/               # Core modules
│   ├── main.py             # FastAPI app
│   └── requirements.txt    # Python dependencies
├── frontend/               # React TypeScript frontend
│   ├── src/pages/         # Page components
│   ├── package.json       # Node dependencies
│   └── vite.config.ts     # Vite configuration
├── notiq_env/             # Python virtual environment
├── .env                   # Environment variables (create this!)
└── README.md              # This file
```

---

## 🔧 Development

### Backend API Documentation

Once backend is running, visit:
```
http://localhost:8000/docs
```

Interactive Swagger UI with all API endpoints!

---

## 📊 Data Collection & ML

The app automatically collects data for future ML model training:

- **Flashcard reviews**: Response quality, timing, SM-2 scores
- **Quiz attempts**: Answers, time spent, accuracy
- **Match games**: Matching accuracy, speed

**ML Readiness Threshold:**
- 20 total interactions
- 5 verified interactions (quizzes/matches)

Check readiness at: `GET /api/stats/ml-readiness`

---

## 🎓 Tech Stack

**Backend:**
- Python 3.11 + FastAPI
- Gemini 2.0 Flash API
- SM-2 Algorithm

**Frontend:**
- React 18 + TypeScript
- Vite + TailwindCSS
- shadcn/ui + TanStack Query

---

**Happy Studying! 📚**
