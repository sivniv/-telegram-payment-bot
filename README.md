# Telegram Payment Reporting Bot

A Python-based Telegram bot that automatically detects, parses, and logs bank payment notifications from `kb_prasac_merchant_payment` system in group chats.

## Features

- 🤖 **Automatic Payment Detection**: Monitors group messages for payment notifications
- 💰 **Smart Parsing**: Extracts payment amount and payer name using RegEx
- 💾 **JSON Storage**: Persistent transaction storage in `transactions.json`
- 📊 **On-Demand Reports**: Generate daily and summary reports via commands
- ⏰ **Scheduled Reports**: Optional daily automated reports
- 🔍 **Robust Filtering**: Ignores non-payment messages

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Create Telegram Bot
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Create a new bot with `/newbot`
3. Copy the bot token

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env and add your bot token
```

### 4. Add Bot to Group
1. Add your bot to the target group chat
2. Give it permission to read messages
3. For scheduled reports, get the group chat ID

### 5. Run the Bot
```bash
python main.py
```

## Bot Commands

- `/daily` - Today's payment report
- `/daily YYYY-MM-DD` - Specific date report  
- `/summary` - All-time summary
- `/help` - Show help message

## Expected Message Format

The bot detects messages containing `kb_prasac_merchant_payment` and parses:

```
kb_prasac_merchant_payment
Payment Notification
Received Payment Amount 4.50 USD
- Paid by: JOHN DOE / Bank Transfer
```

## File Structure

```
├── main.py                 # Main entry point
├── telegram_bot.py         # Bot message handlers and commands
├── payment_parser.py       # RegEx parsing logic
├── transaction_storage.py  # JSON storage management
├── scheduler.py            # Daily report scheduling
├── config.py              # Configuration settings
├── test_parser.py         # Testing script
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
└── transactions.json     # Auto-generated transaction log
```

## Testing

Test the parser functionality:
```bash
python test_parser.py
```

## Configuration

Edit `config.py` to customize:
- Transaction file location
- Payment system identifier
- Daily report time
- Other settings

## Scheduled Reports

To enable automatic daily reports, uncomment and configure the scheduler in `main.py`:

```python
scheduler = DailyReportScheduler(group_chat_id="YOUR_GROUP_CHAT_ID")
scheduler.start_scheduler()
```

## Security

- Store bot token securely in `.env` file
- Don't commit `.env` to version control
- Bot only responds to payment notifications and commands
- No sensitive data is logged or transmitted