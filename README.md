# Mo-football

Mo-football is a Telegram bot starter for football match analysis. It can receive a match image, extract text via OCR, save the image and extracted data, and then query a football API to build a basic statistical probability report.

The project is designed as a starting point for a football analytics bot and is ready to be deployed on Railway.

## Features
- Telegram bot with `/start`, `/help`, and `/analyze`
- Image upload support
- OCR text extraction from uploaded images
- Football data lookup using the football-data API
- Simple statistical probability report for match outcomes
- SQLite storage for uploaded images and saved analyses
- Dockerfile / Railway deployment support

## Tech stack
- Python 3.11+
- FastAPI
- python-telegram-bot
- OCR: Tesseract + Pillow + pytesseract
- HTTP client: httpx
- Data storage: SQLite

## Local setup

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

4. Fill in the required values in `.env`.

5. Install Tesseract OCR on your machine.
   - Ubuntu/Debian:
     ```bash
     sudo apt update && sudo apt install tesseract-ocr
     ```
   - macOS:
     ```bash
     brew install tesseract
     ```
   - Windows: install Tesseract and ensure it is on PATH.

6. Start the app:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## Environment variables

The project expects these variables in `.env`:

```env
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_WEBHOOK_URL=https://your-domain.example.com/webhook
FOOTBALL_DATA_TOKEN=your_football_data_token
DATABASE_PATH=data/bot.db
OCR_LANG=eng
```

## Bot commands

- `/start` — show welcome message
- `/help` — show usage instructions
- `/analyze PL|Arsenal|Chelsea` — analyze a match using the competition code and team names

## Supported competition codes
- PL
- PD
- BL1
- SA
- FL1

## Deployment on Railway

1. Push this repo to GitHub.
2. Create a new Railway project and connect it to the repo.
3. Set these variables in Railway:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_WEBHOOK_URL`
   - `FOOTBALL_DATA_TOKEN`
   - `DATABASE_PATH=data/bot.db`
   - `OCR_LANG=eng`
4. Use the start command:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

5. Make sure Telegram can reach your webhook endpoint.

## Notes

- This bot is a starter analytics project.
- The analysis is based on basic statistical logic and historical team performance; it is not a guarantee of profit or a guaranteed prediction outcome.
- The bot stores uploaded photos and analyses locally in the `data/` folder and the SQLite database.

## License

This project is provided as a starter template and can be adapted freely for personal or commercial work.
