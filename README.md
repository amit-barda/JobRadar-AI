# JobRadar AI

AI-powered job tracking platform for Product and Project Manager roles.

## Quick Start

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
docker compose up --build
```

Open http://localhost:3000 — login with **demo@jobradar.ai / demo123**

## Features

- **Job Collection** — LinkedIn/Glassdoor email alerts, RSS feeds, manual URL paste
- **AI Job Analysis** — Extracts skills, seniority, ATS keywords, red flags
- **CV Upload & Analysis** — PDF/DOCX parsing with AI extraction
- **CV–Job Matching** — ATS-style scoring across 6 weighted dimensions
- **Interview Prep** — AI-generated questions + mock interview mode
- **Cover Letter** — Personalized generation per job
- **Job Tracking** — Kanban-style status management

## Architecture

| Service | Tech | Port |
|---------|------|------|
| Frontend | Next.js 14 + TailwindCSS | 3000 |
| Backend | FastAPI + Python 3.11 | 8000 |
| Database | PostgreSQL 15 | 5432 |
| Queue | Redis 7 + Celery | 6379 |

## Environment Variables

See `.env.example` for all configuration options.

**Required:**
- `OPENAI_API_KEY` — Any OpenAI-compatible API key

## Development

```bash
# Backend only
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend only  
cd frontend && npm install && npm run dev
```

API docs available at http://localhost:8000/docs
