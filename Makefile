.PHONY: help setup install install-dev test test-cov lint format clean run run-saas security docs

# Default target
help:
	@echo "Telegram Payment Bot - Development Commands"
	@echo "=========================================="
	@echo "setup          - Set up development environment"
	@echo "install        - Install production dependencies"
	@echo "install-dev    - Install development dependencies"
	@echo "test           - Run tests"
	@echo "test-cov       - Run tests with coverage report"
	@echo "lint           - Run all linters"
	@echo "format         - Auto-format code"
	@echo "clean          - Clean up cache and build files"
	@echo "run            - Run the simple bot (main.py)"
	@echo "run-saas       - Run the SaaS bot (simple_bot.py)"
	@echo "security       - Run security scans"
	@echo "docs           - Generate documentation"

# Setup development environment
setup:
	python -m venv .venv
	@echo "Virtual environment created. Activate it with:"
	@echo "  source .venv/bin/activate  # On Linux/Mac"
	@echo "  .venv\\Scripts\\activate     # On Windows"
	$(MAKE) install-dev
	pre-commit install
	@echo "Development environment ready!"

# Install dependencies
install:
	pip install --upgrade pip
	pip install -r requirements.txt

install-dev:
	pip install --upgrade pip
	pip install -r requirements-dev.txt

# Testing
test:
	pytest -v

test-cov:
	pytest --cov=. --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/index.html"

# Code quality
lint:
	black --check .
	isort --check-only .
	flake8 .
	mypy . --config-file pyproject.toml || true
	bandit -r . -ll --skip B101,B601

format:
	black .
	isort .

# Cleaning
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.pyd" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true

# Running the bot
run:
	python main.py

run-saas:
	python simple_bot.py

# Security scanning
security:
	bandit -r . -f json -o bandit-report.json
	safety check --json
	@echo "Security reports generated"

# Documentation
docs:
	@echo "Documentation generation not yet configured"
	@echo "Run 'sphinx-quickstart' to set up Sphinx documentation"