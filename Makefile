PYTHON=python3
SRC=app
SHELL=/bin/sh
# Auto-detect pipenv and run tools inside it if available
RUN:=$(shell if command -v pipenv >/dev/null 2>&1 && pipenv --venv >/dev/null 2>&1; then echo "pipenv run"; fi)

.PHONY: format lint type test security hooks all run dev install clean

all: format lint type

format:
	@if $(RUN) ruff --version >/dev/null 2>&1; then \
		echo "[format] ruff found: running 'ruff format .'"; \
		$(RUN) ruff format .; \
		echo "[format] fixing import order via 'ruff check --select I --fix .'"; \
		$(RUN) ruff check --select I --fix .; \
	else \
		echo "[format] ruff not found: skipping ruff formatting"; \
	fi
	$(RUN) isort .
	$(RUN) black .

lint:
	@if $(RUN) ruff --version >/dev/null 2>&1; then \
		$(RUN) ruff check --fix .; \
	else \
		echo "[lint] ruff not found: fixing with isort/black instead"; \
		$(RUN) isort .; \
		$(RUN) black .; \
	fi

type:
	$(RUN) mypy $(SRC)

security:
	$(RUN) bandit -q -r $(SRC)

test:
	$(RUN) pytest -q

hooks:
	$(RUN) pre-commit install
	$(RUN) pre-commit run --all-files

# Development and runtime commands
install:
	@if command -v pipenv >/dev/null 2>&1; then \
		echo "[install] Installing dependencies with pipenv..."; \
		pipenv install --dev; \
	else \
		echo "[install] pipenv not found, using pip..."; \
		pip install -r requirements.txt -r requirements-dev.txt; \
	fi

run:
	@echo "[run] Starting FastAPI server with pipenv..."
	$(RUN) python -m app.main

dev:
	@echo "[dev] Starting FastAPI server in development mode..."
	$(RUN) uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

clean:
	@echo "[clean] Cleaning up cache and temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true