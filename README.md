# SyllabusSync

**AI-powered syllabus parser and autonomous study plan generator.**

Upload your course syllabus (PDF) and our AI agent doesn't just extract dates — it *reasons* about how to break down every assignment, schedules study sessions before exams, and builds a personalized academic plan you can export to Google Calendar.

## How It's Agentic

Traditional automation: "Read dates from PDF → put them on calendar."

**SyllabusSync's AI agent:**
1. **Extracts** all events from unstructured syllabus text (handles tables, relative dates like "Week 5", ambiguous references)
2. **Reasons** about each assignment — a research paper gets broken into: topic selection → research → outline → first draft → revision → final review
3. **Plans autonomously** — schedules study sessions before exams, spaces prep work evenly, respects workload balance
4. **Warns** about heavy weeks, conflicting deadlines, and tight turnarounds

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + TypeScript + Tailwind CSS + Vite |
| Backend | Python + FastAPI |
| PDF Parsing | pdfplumber |
| AI Agent | Groq (Llama 3.3 70B) — free, fast inference |
| Calendar Export | .ics file + Google Calendar links |

## Quick Start

### Backend

```bash
cd backend
pip install -e .

uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173, upload a syllabus PDF, and generate your study plan. No API key needed in the UI — it's handled server-side.

## Architecture

```
User uploads PDF
        │
        ▼
┌─────────────────┐     ┌──────────────────────────────┐
│  React Frontend  │────▶│  Python Backend (FastAPI)     │
│  - File upload   │     │                              │
│  - Event review  │     │  1. pdfplumber: extract text │
│  - Study plan UI │     │  2. Llama 3.3: extract events│
│  - .ics download │     │  3. Llama 3.3: generate study│
│  - GCal links    │◀────│     plan (agentic reasoning) │
└─────────────────┘     └──────────────────────────────┘
```

## License

MIT
