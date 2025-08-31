PYTHON=python3
SRC=app
SHELL=/bin/sh
# Auto-detect pipenv and run tools inside it if available
RUN:=$(shell if command -v pipenv >/dev/null 2>&1 && pipenv --venv >/dev/null 2>&1; then echo "pipenv run"; fi)

.PHONY: format lint type test security hooks all

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
