# Mo-football ⚽

Telegram bot starter for football match analysis. It accepts match images, extracts visible text using OCR, saves images and analyses, and generates a basic probability report from historical match results provided by football-data.org.

> Predictions are statistical estimates only. They are not guaranteed outcomes or profit, and the current model does not account for injuries, lineups, or betting-market odds.

## Bot commands

- `/start` — welcome and usage
- `/help` — help
- `/analyze PL|Arsenal|Chelsea` — analyze a fixture by competition code and team names
- Send a photo — save the image and return OCR text; verify team names manually before analysis

Supported competition codes: `PL`, `PD`, `BL1`, `SA`, `FL1`.

## Required credentials

- `TELEGRAM_BOT_TOKEN`: create a bot with [@BotFather](https://t.me/BotFather).
- `FOOTBALL_DATA_TOKEN`: API token from [football-data.org](https://www.football-data.org/).

Never commit `.env` or send tokens in chat.

## Run locally

Requires Python 3.11+ and Tesseract OCR installed.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set your Telegram and football-data tokens. For local webhook testing, use a public HTTPS tunnel and set `TELEGRAM_WEBHOOK_URL` to its `/webhook` URL. Start the server:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The local health check is `http://localhost:8000/health`. Telegram webhooks require a publicly reachable HTTPS address; localhost alone will not receive Telegram updates.

## Deploy on Railway

1. Create a Railway project and deploy this GitHub repository.
2. The included Dockerfile installs Tesseract and starts Uvicorn using Railway's `$PORT`.
3. Generate a public domain for the service, then set the variables below in Railway. `TELEGRAM_WEBHOOK_URL` must be the full URL ending in `/webhook`.
4. Add a Railway Volume mounted at `/app/data` so SQLite data and uploaded images survive redeployments.
5. Redeploy after setting the variables. Check `/health` and the deployment logs, then send `/start` to your bot.

Required Railway variables:

```text
TELEGRAM_BOT_TOKEN=...                 # from BotFather
FOOTBALL_DATA_TOKEN=...                # from football-data.org
TELEGRAM_WEBHOOK_URL=https://YOUR-DOMAIN/webhook
DATABASE_PATH=/app/data/bot.db
PHOTOS_DIR=/app/data/photos
OCR_LANG=eng
TELEGRAM_WEBHOOK_SECRET=...            # optional; use a random -safe string
```

A suitable start command is already configured by the Dockerfile. If overriding it, use:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Storage and OCR

The default database is SQLite. For Railway, mount persistent storage at `/app/data` and use the paths above. OCR defaults to English (`OCR_LANG=eng`). Arabic OCR requires the Arabic Tesseract language data to be installed in the image and `OCR_LANG=eng+ara`; the default image only installs the English language pack.

## License

Starter software; adapt as needed. Check the terms of any data provider you use.
