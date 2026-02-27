.PHONY: lint format mypy test check fix

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format --check src/ tests/

mypy:
	uv run mypy src/

test:
	uv run pytest --cov=src/clockify_export --cov-report=term-missing

check: lint format mypy test

fix:
	uv run ruff check --fix src/ tests/
	uv run ruff format src/ tests/
