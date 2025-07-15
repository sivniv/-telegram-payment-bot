# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Telegram Payment Bot system with dual architecture:

1. **Simple Bot Mode** (`main.py`) - Public version without authentication for testing
2. **SaaS Mode** (`simple_bot.py`) - Multi-tenant commercial version with client management, authentication, and billing

The bot monitors Telegram groups for payment notifications from various banking systems (KB Prasac, ABA Bank, Wing Money, ACLEDA) and automatically parses, stores, and reports on transactions.

## Development Commands

### Running the Bot
```bash
# Simple/testing mode (current default)
python3 main.py

# SaaS mode with authentication
python3 simple_bot.py

# Install dependencies
pip install -r requirements.txt
```

### Testing
```bash
# Test payment parsing patterns
python3 tests/test_parser.py

# Test configurable bot features  
python3 tests/test_configurable_bot.py

# Run all tests with pytest
pytest tests/

# Use development commands
make test          # Run tests
make test-cov      # Run tests with coverage
make lint          # Run code quality checks
```

### Deployment
- **Railway**: Automatically deploys from GitHub main branch
- **Procfile**: Configured to run `main.py` by default
- Update GitHub repository to trigger Railway deployment

## Core Architecture

### Payment Processing Pipeline
1. **Message Detection**: `PaymentParser.is_payment_message()` checks for payment identifiers
2. **Pattern Matching**: Uses RegEx patterns from `GroupSettingsManager` to extract amount/payer
3. **Storage**: `TransactionStorage` saves to `transactions.json`
4. **Reporting**: Bot commands generate daily/summary reports

### Multi-Source Support
The `GroupSettingsManager` (`group_settings.py`) provides configurable payment source detection:
- **KB Prasac**: Identifier `"Received Payment Amount"`, pattern `r'Received Payment Amount\s+([\d.]+)\s+USD'`
- **ABA Bank**: Identifier `"ABA"`, pattern `r'Amount:\s*USD\s*([\d.]+)'` 
- **Wing Money**: Identifier `"Wing"`, pattern `r'Received\s+([\d.]+)\s+USD'`
- **ACLEDA**: Identifier `"ACLEDA"`, pattern `r'Amount:\s*([\d.]+)\s*USD'`

### SaaS Architecture (when using `simple_bot.py`)
- **Client Management**: `ClientManager` handles subscription plans (Free, Basic, Premium, Enterprise)
- **Authentication**: `AuthMiddleware` enforces group registration and usage limits
- **Multi-tenancy**: Groups must be associated with paying clients
- **Admin Interface**: Commands for client creation, billing, group management

### Configuration Files
- **`.env`**: Bot token and environment variables
- **`group_settings.json`**: Per-group payment source configuration
- **`clients.json`**: SaaS client data and billing information
- **`transactions.json`**: Payment transaction storage

## Key Classes and Responsibilities

- **`PaymentParser`**: RegEx-based payment detection and parsing using group-specific patterns
- **`TransactionStorage`**: JSON-based persistence with daily summary generation
- **`GroupSettingsManager`**: Payment source configuration per Telegram group
- **`ClientManager`**: SaaS subscription and billing management (Free: 1000 tx, Basic: $4.99/3000 tx, Premium: $9.99/10000 tx, Enterprise: $19.99/100000 tx)
- **`AuthMiddleware`**: Group authentication and feature access control

## Project Structure

```
telegram-payment-bot/
├── docs/business/          # Commercial documentation
├── tests/                  # Test files  
├── main.py                # Simple bot (testing mode)
├── simple_bot.py          # SaaS bot (production mode)
├── config.py              # Centralized configuration
├── payment_parser.py      # Payment message parsing
├── transaction_storage.py # Data persistence
├── group_settings.py      # Group configuration
└── client_manager.py      # SaaS client management
```

## Business Documentation

Complete commercial documentation suite in `docs/business/`:
- `COMMERCIAL_PROPOSAL.md`: Sales presentation and pricing
- `SERVICE_AGREEMENT.md`: Legal terms and SLA
- `ONBOARDING_GUIDE.md`: Client setup process
- `PRIVACY_POLICY.md`: GDPR/CCPA compliance
- `PAYMENT_TERMS.md`: Billing procedures

## Mode Switching

To switch between simple and SaaS modes:
1. **For Testing**: Use `main.py` (no authentication, processes all groups)
2. **For Commercial**: Use `simple_bot.py` (requires client registration via admin commands)
3. **Update Procfile**: Change which file Railway executes on deployment

The current deployment runs the simple mode for testing payment detection before adding commercial features.