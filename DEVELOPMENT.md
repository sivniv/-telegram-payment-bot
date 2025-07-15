# Development Guide

This guide covers setting up and working with the Telegram Payment Bot development environment.

## Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd telegram-payment-bot

# Run the setup script
./scripts/dev-setup.sh

# Or use make
make setup
```

## Development Environment

### Prerequisites

- Python 3.11 or higher
- Git
- Make (optional but recommended)

### Virtual Environment

We use Python virtual environments to isolate dependencies:

```bash
# Create virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements-dev.txt
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
BOT_TOKEN=your_telegram_bot_token
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## Development Workflow

### 1. Before Starting Work

```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Update dependencies
pip install -r requirements-dev.txt

# Install/update pre-commit hooks
pre-commit install
```

### 2. Making Changes

Follow the coding standards:
- Code is formatted with Black (100 char line length)
- Imports are sorted with isort
- Code is linted with Flake8
- Type hints are checked with mypy

### 3. Before Committing

Pre-commit hooks will automatically run, but you can also run manually:

```bash
# Format code
make format

# Run linters
make lint

# Run tests
make test
```

### 4. Commit Message Format

We use conventional commits:
```
type(scope): subject

body (optional)

footer (optional)
```

Types: feat, fix, docs, style, refactor, test, chore

Example:
```
feat(parser): add support for ACLEDA bank messages
```

## Available Commands

### Using Make

```bash
make help          # Show all available commands
make setup         # Set up development environment
make install       # Install production dependencies
make install-dev   # Install development dependencies
make test          # Run tests
make test-cov      # Run tests with coverage
make lint          # Run all linters
make format        # Auto-format code
make clean         # Clean cache files
make run           # Run simple bot
make run-saas      # Run SaaS bot
make security      # Run security scans
```

### Manual Commands

```bash
# Testing
pytest                           # Run all tests
pytest tests/test_parser.py      # Run specific test
pytest -v --tb=short            # Verbose with short traceback
pytest --cov=. --cov-report=html # With coverage

# Code Quality
black .                          # Format code
isort .                          # Sort imports
flake8 .                         # Lint code
mypy .                           # Type checking
bandit -r .                      # Security scan

# Running the Bot
python main.py                   # Simple mode
python simple_bot.py             # SaaS mode
```

## Project Structure

```
telegram-payment-bot/
├── .github/workflows/       # CI/CD pipelines
├── .vscode/                # VS Code settings
├── scripts/                # Development scripts
├── tests/                  # Test files
├── main.py                 # Simple bot entry point
├── simple_bot.py           # SaaS bot entry point
├── payment_parser.py       # Payment message parser
├── transaction_storage.py  # Transaction persistence
├── group_settings.py       # Group configuration
├── client_manager.py       # SaaS client management
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development dependencies
├── pyproject.toml         # Python project config
├── setup.cfg              # Tool configurations
├── .flake8                # Flake8 config
├── .pre-commit-config.yaml # Pre-commit hooks
└── Makefile               # Development commands
```

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest tests/test_parser.py

# Run tests matching pattern
pytest -k "test_parse"

# Run with debugging
pytest -vv --tb=long
```

### Writing Tests

Tests are located in the `tests/` directory. Follow these conventions:
- Test files: `test_*.py`
- Test classes: `TestClassName`
- Test functions: `test_function_name`

Example test:
```python
import pytest
from payment_parser import PaymentParser

def test_parse_kb_prasac_payment():
    parser = PaymentParser()
    message = "Received Payment Amount 50.00 USD from John Doe"
    result = parser.parse_payment(message, "kb_prasac")
    
    assert result is not None
    assert result['amount'] == 50.00
    assert result['payer'] == "John Doe"
```

## Debugging

### VS Code Debugging

Debug configurations are provided in `.vscode/launch.json`:
- **Python: Main Bot** - Debug main.py
- **Python: SaaS Bot** - Debug simple_bot.py
- **Python: Debug Current File** - Debug active file
- **Python: Pytest** - Debug tests

### Command Line Debugging

```python
# Add breakpoints in code
import pdb; pdb.set_trace()

# Or use the debugger
python -m pdb main.py
```

## Code Style Guide

### Python Style

- Follow PEP 8 with 100 character line limit
- Use type hints for function parameters and returns
- Write docstrings for all public functions/classes
- Keep functions focused and under 50 lines

### Example:

```python
from typing import Optional, Dict

def parse_payment(self, message: str, source: str) -> Optional[Dict[str, Any]]:
    """
    Parse payment information from a message.
    
    Args:
        message: The raw message text
        source: Payment source identifier (kb_prasac, aba, etc.)
    
    Returns:
        Dict with payment details or None if not a payment message
    """
    # Implementation here
```

## Security

### Security Scanning

```bash
# Run Bandit security scan
make security

# Or manually
bandit -r . -ll --skip B101,B601

# Check dependencies
safety check
```

### Security Best Practices

1. Never commit sensitive data (.env, tokens, passwords)
2. Use environment variables for configuration
3. Validate all user inputs
4. Keep dependencies updated
5. Run security scans before releases

## Continuous Integration

GitHub Actions workflows run on every push and PR:

1. **Linting** - Code style checks
2. **Testing** - Unit tests with coverage
3. **Security** - Vulnerability scanning
4. **Build** - Verification of imports and setup

### Running CI Locally

```bash
# Simulate CI environment
act push -j lint
act push -j test
act push -j security
```

## Deployment

### Railway Deployment

Deployments happen automatically when pushing to main:

```bash
# Deploy manually
railway up

# Check logs
railway logs
```

### Environment Configuration

Set these in Railway dashboard:
- `BOT_TOKEN` - Your Telegram bot token
- `ENVIRONMENT` - production
- `LOG_LEVEL` - INFO or ERROR

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure virtual environment is activated
2. **Bot not responding**: Check BOT_TOKEN in .env
3. **Tests failing**: Update dependencies with `pip install -r requirements-dev.txt`
4. **Pre-commit failing**: Run `make format` to auto-fix

### Getting Help

1. Check existing issues on GitHub
2. Read the error messages carefully
3. Use debug mode for detailed logs
4. Ask in project discussions

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit with conventional commits
6. Push and create a Pull Request

## Resources

- [Python Telegram Bot Documentation](https://python-telegram-bot.org/)
- [Black Code Style](https://black.readthedocs.io/)
- [pytest Documentation](https://docs.pytest.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)