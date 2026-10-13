# TutorAI

TutorAI is a local-first AI tutor and mentor. It will learn how a learner
prefers to study, create an adaptive learning plan, find cited resources, and
track progress.

## Phase 2 foundation

This phase provides:

- A FastAPI backend with a health endpoint.
- A local SQLite learner profile with Alembic migrations.
- One-question-at-a-time onboarding and editable profile endpoints.
- A provider-neutral async LLM interface with Anthropic Claude and Google
  Gemini adapters.
- TutorAI system prompt, contextual chat orchestration, answer logging, and
  wrong-answer reports.
- Persisted learning plans with modules, structured lessons, practice tasks,
  quizzes, and lesson progress.
- A React + TypeScript + Vite frontend shell.
- Python pytest and frontend Vitest test runners.
- A `.env.example` file for future provider and resource credentials.
- A Makefile for setup and local commands.

TutorAI stores onboarding answers locally in SQLite. Preferences are stored as
adjustable profile data, not as permanent learning-style labels.

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

No API keys are needed to run the local foundation without model calls.

To use the Phase 4 model providers, set `LLM_PROVIDER` and the matching API
key in `.env`. The provider factory rejects missing keys and unsupported
provider names rather than silently selecting a fallback.

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-key
```

Or:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-key
```

The adapters are not called by the onboarding routes yet; tutor orchestration
is available through `POST /api/chat`.

Initialize the Phase 3 database after setup:

```bash
make migrate
```

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

Phase 3 API endpoints:

- `GET /api/onboarding/questions` — return the next onboarding question.
- `POST /api/onboarding/answers` — save one answer and advance one step.
- `GET /api/profile` — return the saved learner profile.
- `PUT /api/profile` — edit profile fields and preferences.
- `POST /api/chat` — ask TutorAI a question with optional conversation history.
- `POST /api/chat/{answer_id}/report` — report a potentially wrong answer.
- `POST /api/plans` — generate and store a learner-specific roadmap.
- `GET /api/plans/latest` — retrieve the latest roadmap and its lessons.
- `PATCH /api/lessons/{lesson_id}/progress` — update lesson progress.

Chat answers are logged locally with their provider and model metadata. Source
citation support will be connected when the resource finder is implemented.

Learning plans are validated before storage. Each generated lesson must include
a goal, plain-language explanation, two or three examples, a practice task,
at least one quiz question, and an estimated duration.

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
