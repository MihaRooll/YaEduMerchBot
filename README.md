# YaEduMerchBot

Telegram bot for Yandex Educational Merchandise

## Description

YaEduMerchBot is a Telegram bot designed to handle educational merchandise operations for Yandex. This bot provides an interface for users to browse, order, and manage educational materials and merchandise.

## Features

- 🛍️ Browse merchandise catalog
- 📦 Order management
- 👤 User profile management
- 📊 Admin dashboard
- 💳 Payment integration

## Installation

1. Clone the repository:
```bash
git clone https://github.com/MihaRooll/YaEduMerchBot.git
cd YaEduMerchBot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the bot:
```bash
python main.py
```

## Configuration

Create a `.env` file with the following variables:

```
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=your_database_url
ADMIN_IDS=comma_separated_admin_ids
PAYMENT_TOKEN=your_payment_provider_token
```

## Project Structure

```
YaEduMerchBot/
├── main.py              # Bot entry point
├── bot/                 # Bot logic
│   ├── __init__.py
│   ├── handlers/        # Message handlers
│   ├── keyboards/       # Inline keyboards
│   ├── middlewares/     # Bot middlewares
│   └── utils/           # Utility functions
├── database/            # Database models and operations
├── config/              # Configuration files
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
└── README.md           # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
