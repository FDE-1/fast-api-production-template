PYTHON := .venv/bin/python
PIP := $(PYTHON) -m pip

.PHONY: install lint typecheck test all clean venv

venv:
	python3.14 -m venv .venv
	$(PIP) install --upgrade pip

install: venv
	$(PIP) install -e ".[dev]"
	.venv/bin/pre-commit install

lint:
	.venv/bin/ruff check src/ tests/
	.venv/bin/ruff format --check src/ tests/

format:
	.venv/bin/ruff format src/ tests/
	.venv/bin/ruff check --fix src/ tests/

typecheck:
	.venv/bin/mypy src/ tests/

test:
	.venv/bin/pytest

all: lint typecheck test
	@echo "✅ All checks passed"

clean:
	rm -rf .mypy_cache .pytest_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
