VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: install dev test lint format typecheck start clean

install: $(VENV)/bin/activate
	$(PIP) install -e ".[dev]"
	cd frontend && npm install
	$(VENV)/bin/pre-commit install
	$(VENV)/bin/pre-commit install --hook-type pre-push
	$(VENV)/bin/pre-commit autoupdate

$(VENV)/bin/activate:
	python3 -m venv $(VENV)

dev:
	$(VENV)/bin/uvicorn stamped.api.main:app --reload --port 8421 &
	cd frontend && npm run dev

test: test-backend test-frontend

test-backend:
	$(VENV)/bin/pytest backend/tests/ -v --tb=short --cov=backend/stamped --cov-report=xml --cov-report=term-missing

test-frontend:
	cd frontend && npm run test:unit -- --coverage --run

lint: lint-backend lint-frontend

lint-backend:
	$(VENV)/bin/ruff check backend/
	$(VENV)/bin/ruff format --check backend/
	$(VENV)/bin/mypy backend/

lint-frontend:
	cd frontend && npm run lint
	cd frontend && npm run type-check

format:
	$(VENV)/bin/ruff check --fix backend/
	$(VENV)/bin/ruff format backend/

start:
	$(VENV)/bin/stamped start

clean:
	rm -rf $(VENV) frontend/node_modules frontend/dist coverage.xml .coverage .mypy_cache .ruff_cache .pytest_cache
