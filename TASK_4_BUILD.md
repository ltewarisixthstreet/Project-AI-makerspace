# Task 4: Building End-to-End Agentic RAG Prototype

**Deadline:** July 16, 2026  
**Status:** In Progress  
**Goal:** Build, test, and deploy a production-ready Financial Advisor AI

---

## Overview

This task implements the complete Financial Advisor AI system with three components:

1. **RAG Notebook** (`02_Financial_Advisor_RAG.ipynb`) — Development & testing
2. **FastAPI Backend** (`backend_main.py`) — REST API + Agent
3. **Next.js Frontend** (`frontend_app.tsx`) — Chat UI + Session Management

Together, these form a browser-runnable web app deployable to Vercel + Render.

---

## Architecture Reminder

```
Browser (Next.js)
     ↓ (HTTP/WebSocket)
Backend (FastAPI)
     ├─ RAG Pipeline (LangChain)
     ├─ Vector Store (Qdrant)
     ├─ LLM (Claude)
     └─ Memory (Redis/in-memory)
```

---

## Part 1: Local Development Setup

### Step 1.1: Clone/Organize Project Structure

```
Project-AI-makerspace/
├── Were-Talking-Millions.pdf          # Knowledge base
├── 02_Financial_Advisor_RAG.ipynb      # Development notebook
├── backend_main.py                     # FastAPI backend
├── requirements.txt                    # Python dependencies
├── .env.example                        # Environment template
├── frontend/                           # Next.js app (create this)
│   ├── package.json
│   ├── app/
│   │   ├── page.tsx
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── next.config.js
│   └── tsconfig.json
└── README.md
```

### Step 1.2: Set Up API Keys

1. Get API keys:
   - **OpenAI** (embeddings): https://platform.openai.com/api-keys
   - **Anthropic** (Claude): https://console.anthropic.com/
   - **Tavily** (web search): https://tavily.com/ (optional)

2. Create `.env` file:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

### Step 1.3: Set Up Python Backend

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Verify Installation:**
```bash
python -c "import langchain; import fastapi; print('✓ Setup successful')"
```

### Step 1.4: Test RAG Notebook (Development)

1. Open `02_Financial_Advisor_RAG.ipynb` in Jupyter/VS Code
2. Run cells sequentially
3. Verify:
   - ✅ PDF loads successfully
   - ✅ Chunks are created (should see ~100-150 chunks)
   - ✅ Embeddings work
   - ✅ Qdrant vector store builds
   - ✅ Retrieval returns relevant chunks
   - ✅ Claude generates coherent financial advice

**Expected Output Example:**
```
Question: "What's a realistic asset allocation for someone 35 years old with $500k saved?"

Answer: "For a 35-year-old with a 25-year time horizon, a common starting point is the 'age in bonds' rule—roughly 35% bonds and 65% stocks. This gives you growth potential while providing stability. However, here are key considerations: 1) Your income stability: if you have stable W2 income, you can lean more aggressive. 2) Major expenses ahead: house down payment in 5 years? Shift more to bonds. 3) Risk tolerance: if a 30% market drop would stress you, reduce stocks. A realistic allocation considering you want to retire at 60 might be 70% stocks, 25% bonds, 5% cash for flexibility..."

Sources:
[Source 1] Were-Talking-Millions.pdf, page 42 (relevance: 0.878)
```

---

## Part 2: Run Backend Locally

### Step 2.1: Start FastAPI Server

```bash
cd /path/to/Project-AI-makerspace
python backend_main.py
```

**Expected Output:**
```
================================================================================
🚀 Financial Advisor AI Backend
================================================================================
Starting FastAPI server...
📚 RAG Pipeline: text-embedding-3-small + claude-3-5-sonnet-20241022
🗄️  Vector Store: Qdrant (in-memory)
📖 Knowledge Base: Were-Talking-Millions.pdf
================================================================================

INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 2.2: Test Backend API

**Health Check:**
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","rag_ready":true,"timestamp":"..."}
```

**Test Chat Endpoint:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "message": "What is asset allocation?",
    "session_id": "session_123",
    "user_context": {
      "salary": 150000,
      "assets": 500000,
      "timeline_years": 25,
      "risk_tolerance": "moderate"
    }
  }'
```

**Expected Response:**
```json
{
  "session_id": "session_123",
  "user_message": "What is asset allocation?",
  "assistant_response": "Asset allocation is the process of dividing your investments across different asset classes...",
  "sources": [
    {
      "source_label": "Source 1",
      "file": "Were-Talking-Millions.pdf",
      "page": 42,
      "relevance_score": 0.87
    }
  ],
  "num_chunks_retrieved": 4,
  "timestamp": "2026-07-12T..."
}
```

---

## Part 3: Set Up Frontend

### Step 3.1: Create Next.js Project Structure

```bash
# From project root
mkdir frontend
cd frontend
npm create-next-app@latest . --typescript --tailwind

# Or manually:
# - Copy frontend_package.json to package.json
# - Create app/ directory with page.tsx and layout.tsx
```

### Step 3.2: Configure Frontend

**`frontend/app/page.tsx`:**
- Use the `frontend_app.tsx` content provided
- This is your main chat interface

**`frontend/app/layout.tsx`:**
```tsx
export const metadata = {
  title: 'Financial Advisor AI',
  description: 'Intelligent financial guidance powered by RAG',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
```

**`frontend/app/globals.css`:**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

html {
  scroll-behavior: smooth;
}
```

**`frontend/.env.local`:**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Step 3.3: Start Frontend Dev Server

```bash
cd frontend
npm install
npm run dev
```

**Expected Output:**
```
  ▲ Next.js 14.0.0
  - Local:        http://localhost:3000
```

Open **http://localhost:3000** in your browser.

---

## Part 4: End-to-End Test

### Test Scenario 1: Basic Q&A

1. **Frontend:** Fill in financial profile
   - Salary: $180,000
   - Assets: $500,000
   - Timeline: 25 years
   - Risk: Moderate

2. **Ask Question:** "What's a realistic asset allocation?"

3. **Expected:**
   - ✅ Message sends to backend
   - ✅ Backend retrieves relevant PDF chunks
   - ✅ Claude generates personalized answer
   - ✅ Sources cited with page numbers
   - ✅ Response appears in chat UI in ~3-5 seconds

### Test Scenario 2: Complex Decision

1. **Ask:** "I just got a $150k bonus. Should I max my Roth backdoor or invest in taxable? I'm in the 35% bracket."

2. **Expected:**
   - ✅ Backend retrieves 4-5 relevant chunks about Roth, tax brackets, investing
   - ✅ Claude synthesizes a decision framework (not just yes/no)
   - ✅ References tax implications from PDF
   - ✅ Acknowledges behavioral factors

### Test Scenario 3: Out-of-Scope Question

1. **Ask:** "What stock should I buy right now?"

2. **Expected:**
   - ✅ System redirects: "I don't provide specific stock recommendations..."
   - ✅ Offers alternative: "I can help you evaluate how to choose investments..."

---

## Part 5: Prepare for Deployment

### Step 5.1: Create Deployment Configs

**Backend Deployment (Render):**

1. Create `render.yaml` in project root:
```yaml
services:
  - type: web
    name: financial-advisor-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python backend_main.py
    envVars:
      - key: OPENAI_API_KEY
        sync: false
      - key: ANTHROPIC_API_KEY
        sync: false
      - key: PORT
        value: "8000"
```

2. Set environment variables in Render dashboard:
   - `OPENAI_API_KEY`
   - `ANTHROPIC_API_KEY`

**Frontend Deployment (Vercel):**

1. In `frontend/`, create `vercel.json`:
```json
{
  "env": {
    "NEXT_PUBLIC_API_URL": "@api-url"
  }
}
```

2. Connect GitHub repo to Vercel (or manual deployment)

### Step 5.2: Pre-Deployment Checklist

- [ ] Backend starts without errors
- [ ] All API endpoints tested locally
- [ ] Frontend connects to backend
- [ ] Chat works end-to-end
- [ ] API keys are set (not hardcoded)
- [ ] `.env` is in `.gitignore`
- [ ] PDF file is in the repo (or specify path)
- [ ] Requirements.txt is up to date

---

## Part 6: Deploy to Production

### Option A: Render + Vercel (Recommended)

**Backend (Render):**
```bash
# 1. Push code to GitHub
git add .
git commit -m "Task 4: End-to-end RAG prototype"
git push origin main

# 2. Go to render.com
# 3. New → Web Service → Connect GitHub repo
# 4. Set environment variables
# 5. Deploy
```

**Frontend (Vercel):**
```bash
# 1. Inside frontend/ directory
cd frontend

# 2. Deploy
npm install -g vercel
vercel

# 3. Follow prompts
# 4. Set environment variable: NEXT_PUBLIC_API_URL = [Render backend URL]
```

### Option B: Docker Compose (Local Testing)

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./Were-Talking-Millions.pdf:/app/Were-Talking-Millions.pdf

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend
```

Run:
```bash
docker-compose up
```

---

## Part 7: Testing & Validation

### Functional Tests

**Retrieval Quality:**
- [ ] Relevant chunks are retrieved for financial questions
- [ ] Similarity scores are reasonable (0.7+)
- [ ] Out-of-scope questions don't force fake answers

**Response Quality:**
- [ ] Answers ground in PDF sources
- [ ] Decision frameworks are clear (not just yes/no)
- [ ] Behavioral factors acknowledged
- [ ] No hallucinations (made-up data)

**UI/UX:**
- [ ] Chat works on mobile & desktop
- [ ] Session persists across messages
- [ ] User context form is intuitive
- [ ] Sources are clickable/visible

### Load Testing (Optional)

```bash
# Simple load test
for i in {1..10}; do
  curl -X POST http://localhost:8000/chat \
    -H "Content-Type: application/json" \
    -d '{"user_id": "user_'$i'", "message": "What is asset allocation?"}' &
done
wait
```

Expected: All requests complete within 5-10 seconds each.

---

## Part 8: Post-Deployment Checklist

- [ ] Backend deployed and responding
- [ ] Frontend deployed and loads
- [ ] Chat works end-to-end
- [ ] API keys are secure (not in logs)
- [ ] CORS is properly configured
- [ ] Session management works
- [ ] Performance is acceptable (<3s per response)
- [ ] Error handling is graceful
- [ ] Monitoring/logging is set up

---

## Troubleshooting

### Backend Issues

**"ModuleNotFoundError: No module named 'langchain'"**
```bash
pip install -r requirements.txt
python -m pip show langchain  # Verify installation
```

**"FileNotFoundError: Were-Talking-Millions.pdf"**
- Ensure PDF is in the backend's working directory
- Or specify absolute path in `backend_main.py`

**"OPENAI_API_KEY not set"**
- Check `.env` file exists and has valid keys
- `echo $OPENAI_API_KEY` to verify

### Frontend Issues

**"Cannot find module 'axios'"**
```bash
cd frontend
npm install axios
```

**"API_URL returns 404"**
- Verify backend is running on `localhost:8000`
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- CORS headers in backend (should allow `*` for development)

---

## Success Metrics

✅ **Task 4 Complete When:**

1. Notebook (`02_Financial_Advisor_RAG.ipynb`) runs end-to-end without errors
2. Backend (`backend_main.py`) starts and responds to `/chat` requests
3. Frontend loads on `localhost:3000`
4. Chat works: user → backend → Claude → user
5. Retrieved sources are relevant and cited
6. App works on mobile & desktop browsers
7. Deployed to public URL (Render + Vercel)
8. Response time is <5 seconds per message

---

## Next Steps (Task 5 & Beyond)

Once Task 4 is complete:
- **Task 5:** Build evaluation harness (test dataset, quality metrics)
- **Task 6:** Implement advanced retrieval (re-ranking, filtering)
- **Task 7:** Reflect and finalize for demo day

---

## Files Reference

| File | Purpose |
|------|---------|
| `02_Financial_Advisor_RAG.ipynb` | Development & testing |
| `backend_main.py` | FastAPI server + RAG |
| `requirements.txt` | Python dependencies |
| `frontend_app.tsx` | Chat UI component |
| `frontend_package.json` | Frontend dependencies |
| `.env.example` | Environment template |
| `TASK_4_BUILD.md` | This guide |

---

## Questions & Debugging

For issues:
1. Check logs: `tail -f backend.log` or browser console
2. Verify API keys with quick test
3. Ensure PDF is readable: `python -c "from PyPDF2 import PdfReader; print(PdfReader('Were-Talking-Millions.pdf').pages)"`
4. Test retrieval separately in notebook before running full system
