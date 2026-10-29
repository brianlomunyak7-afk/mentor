# TutorAI

TutorAI is a local-first AI tutor and mentor. It will learn how a learner
prefers to study, create an adaptive learning plan, find cited resources, and
track progress.

## Phase 2 foundation

This phase provides:

- A FastAPI backend with a health endpoint.
- A React + TypeScript + Vite frontend shell.
- Python pytest and frontend Vitest test runners.
- A `.env.example` file for future provider and resource credentials.
- A Makefile for setup and local commands.

Feature work is intentionally added in later phases.

## Setup

Requirements:

- Python 3.12+
- Node.js 20+
- npm

From the project root:

```bash
make setup
cp .env.example .env
```

No API keys are needed to run the Phase 2 foundation.

## Run locally

Use two terminals:

```bash
make backend
```

```bash
make frontend
```

URLs:

- App: http://localhost:5173
- API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Test

```bash
make test
```

## Planned architecture

The backend will expose versioned API routes and services for learner
profiles, plans, lessons, resources, quizzes, progress, notes, and exports.
The frontend will consume those routes through a typed API client. SQLite will
keep local learner data on the user's machine, while configured model APIs will
receive only the context required for a tutor response.
