.PHONY: install dev test lint type-check coverage clean build publish

## Install production dependencies
install:
	pip install -e .

## Install with dev dependencies
dev:
	pip install -e ".[dev]"
	pre-commit install

## Run tests
test:
	pytest tests/ -v

## Run linter
lint:
	ruff check src/ tests/

## Run type checker
type-check:
	mypy src/draft_protocol/ --ignore-missing-imports

## Run tests with coverage
coverage:
	pytest tests/ -v --cov=draft_protocol --cov-report=term-missing --cov-report=html

## Build distribution
build: clean
	python -m build

## Publish to PyPI (requires twine + credentials)
publish: build
	twine upload dist/*

## Clean build artifacts
clean:
	rm -rf dist/ build/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage

## Run all checks (what CI does)
check: lint type-check test

## Show help
help:
	@echo "Available targets:"
	@echo "  make dev         Install with dev dependencies + pre-commit hooks"
	@echo "  make test        Run test suite"
	@echo "  make lint        Run ruff linter"
	@echo "  make type-check  Run mypy type checker"
	@echo "  make coverage    Run tests with coverage report"
	@echo "  make check       Run lint + type-check + test (CI equivalent)"
	@echo "  make build       Build distribution packages"
	@echo "  make publish     Build and publish to PyPI"
	@echo "  make clean       Remove build artifacts"
