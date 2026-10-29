.PHONY: setup migrate backend frontend run test

setup:
	python3 -m venv backend/.venv
	backend/.venv/bin/pip install -e "backend[dev]"
	cd frontend && npm install

migrate:
	backend/.venv/bin/alembic -c backend/alembic.ini upgrade head

backend:
	backend/.venv/bin/uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev -- --host 0.0.0.0

run:
	@echo "Run 'make backend' and 'make frontend' in separate terminals."

test:
	backend/.venv/bin/pytest backend/tests
	cd frontend && npm test
