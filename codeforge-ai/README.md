# CodeForge AI

An AI-powered coding practice platform built with FastAPI, Next.js, and Monaco Editor.
Original black-and-white liquid-glass design system.

## Architecture

```
codeforge-ai/
├── backend/          # FastAPI + PostgreSQL + Redis
│   ├── app/
│   │   ├── api/      # Route handlers (auth, problems, submissions, ai, admin...)
│   │   ├── core/     # Config, security, dependencies
│   │   ├── models/   # SQLAlchemy models
│   │   ├── schemas/  # Pydantic request/response schemas
│   │   ├── services/ # Business logic (mistral, code execution, validation...)
│   │   ├── repositories/ # Data access layer
│   │   ├── workers/  # Background tasks (celery/arq)
│   │   ├── utils/    # Helpers
│   │   └── migrations/
│   └── tests/
├── frontend/         # Next.js + React + TypeScript + Monaco + Tailwind
└── docker/           # Docker configuration
```

## Tech Stack

| Layer   | Technology                              |
|---------|-----------------------------------------|
| Backend | FastAPI, Python 3.12, SQLAlchemy, Alembic |
| Database| PostgreSQL                              |
| Cache   | Redis                                   |
| Auth    | JWT + bcrypt                            |
| AI      | Mistral API (abstracted service layer)  |
| Code Exec | Isolated Docker sandboxes (worker)   |
| Frontend| Next.js 14, React 18, TypeScript        |
| Editor  | Monaco Editor                          |
| Styling | Tailwind CSS + shadcn/ui               |
| Animation| Framer Motion                         |
| Icons   | Lucide React                           |
| State   | TanStack Query + Zustand              |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.12
- Node.js 18+
- Mistral API key

### Development

```bash
# Clone and enter repo
cd codeforge-ai

# Copy environment
cp backend/.env.example backend/.env
# Edit backend/.env with your values

# Start infrastructure (Postgres, Redis)
docker compose up -d postgres redis

# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### Environment Variables

See `backend/.env.example`.

Required:
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection string
- `JWT_SECRET` — Secret key for JWT signing
- `MISTRAL_API_KEY` — Mistral API key

Optional:
- `CORS_ORIGINS` — Comma-separated allowed origins
- `CODE_EXECUTION_TIMEOUT` — Execution timeout in seconds (default 10)
- `CODE_EXECUTION_MEMORY_LIMIT` — Memory limit in MB (default 256)

### Docker

```bash
docker compose up --build
```

### API Documentation

Once the backend is running:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health: http://localhost:8000/health

### Database Migrations

```bash
# Generate new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Testing

```bash
# Backend
cd backend
pytest

# Frontend (after setup)
cd frontend
npm test
```

## Features

- Browse and solve original coding problems
- Monaco editor with syntax highlighting
- Secure isolated code execution
- AI-powered coding assistant (Mistral)
- Admin AI problem generator
- AI test case generation with verification
- Problem quality checker
- User dashboard with activity heatmap
- Leaderboard
- Discussion system
- Contest system
- Full JWT authentication
- Responsive black-and-white liquid-glass UI

## Security

- Code execution is isolated in Docker containers with CPU/memory/time limits
- No code runs inside the FastAPI process
- Hidden test cases are never exposed to the frontend
- Reference solutions are never exposed through public APIs
- Passwords are hashed with bcrypt
- Admin routes require ADMIN role
- Rate limiting on login, registration, submissions, and AI endpoints
