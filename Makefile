# Developer shortcuts for ai-automation-agent.
#
# Usage:
#   make install    Create venv and install all dependencies
#   make dev        Start the dev server with auto-reload
#   make seed       Seed the database with guest user + demo runs
#   make migrate    Apply all pending database migrations
#   make test       Run the Python test suite
#   make lint       Ruff + mypy
#   make clean      Remove venv, caches, and local DB
#
# All commands use the project-local venv so you never depend on system
# Python or manually activated environments. Zero-friction per ADR 001.

PY := .venv/bin/python
PIP := .venv/bin/pip
UVICORN := .venv/bin/uvicorn
ALEMBIC := .venv/bin/alembic
PYTEST := .venv/bin/pytest
RUFF := .venv/bin/ruff
MYPY := .venv/bin/mypy

# Detect a system Python interpreter (prefer 3.12 which matches our pins).
PYTHON_SYS := $(shell command -v python3.12 || command -v python3)

.PHONY: help install dev seed migrate migrate-create test lint clean reset-db freeze

help:
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: .venv ## Create venv and install Python dependencies
	$(PIP) install --upgrade pip --quiet
	$(PIP) install -r requirements.txt
	@echo "✓ Dependencies installed in .venv/"

.venv:
	$(PYTHON_SYS) -m venv .venv

dev: ## Start the FastAPI dev server with auto-reload
	$(UVICORN) app.main:app --reload

seed: ## Seed guest user + demo runs (idempotent)
	$(PY) scripts/seed.py

migrate: ## Apply all pending database migrations
	$(ALEMBIC) upgrade head

migrate-create: ## Generate a new migration (requires MSG="description")
	@if [ -z "$(MSG)" ]; then echo "Usage: make migrate-create MSG='short description'"; exit 1; fi
	$(ALEMBIC) revision --autogenerate -m "$(MSG)"

test: ## Run the Python test suite
	$(PYTEST) tests/ -v

test-quick: ## Run tests quietly (for pre-commit-ish use)
	$(PYTEST) tests/ -q

lint: ## Run ruff + mypy
	$(RUFF) check app/ tests/ agent/
	$(MYPY) app/ --ignore-missing-imports

format: ## Auto-fix lint issues where safe
	$(RUFF) check --fix app/ tests/ agent/
	$(RUFF) format app/ tests/ agent/

reset-db: ## Drop the local SQLite DB and re-migrate + re-seed
	rm -f app.db
	$(MAKE) migrate
	$(MAKE) seed

freeze: ## Pin current installed versions to requirements-lock.txt
	$(PIP) freeze > requirements-lock.txt
	@echo "✓ requirements-lock.txt updated"

clean: ## Remove venv, caches, coverage, local DB
	rm -rf .venv .pytest_cache .ruff_cache .mypy_cache htmlcov
	rm -f app.db .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleaned"
