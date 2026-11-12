# Mo-football ⚽

Telegram bot starter for football match analysis. It accepts match images, extracts visible Arabic and English text using OCR, saves images and analyses, and generates a basic probability report from historical match results provided by football-data.org.

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

## Deploy on Railway

1. Create a Railway project and deploy this GitHub repository.
2. The included Dockerfile installs Python dependencies and Arabic/English Tesseract language data, then starts the web service on Railway's `$PORT`.
3. Generate a public domain for the service.
4. Add the Railway variables below. Set `TELEGRAM_WEBHOOK_URL` to the generated domain with `/webhook` appended.
5. Add a Railway Volume mounted at `/app/data` so the SQLite database and uploaded images survive redeployments.
6. Redeploy after setting variables and the volume. Check `/health`, then send `/start` to your bot.

Required Railway variables:

```text
TELEGRAM_BOT_TOKEN=...                 # from BotFather
FOOTBALL_DATA_TOKEN=...                # from football-data.org
TELEGRAM_WEBHOOK_URL=https://YOUR-DOMAIN/webhook
TELEGRAM_WEBHOOK_SECRET=...             # optional random string using letters, numbers, _ or -
DATABASE_PATH=/app/data/bot.db
PHOTOS_DIR=/app/data/photos
OCR_LANG=eng+ara
```

The Dockerfile already provides the start command. If you override it, use:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Local run

Requires Python 3.11+ and Tesseract OCR with English and Arabic language data.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env`, then run:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

A local server is not reachable by Telegram. For local bot testing, use an HTTPS tunnel and configure `TELEGRAM_WEBHOOK_URL` with its public `/webhook` URL. `/health` should return `{"status":"ok","service":"Mo-football"}`.

## Storage and analysis notes

The default database and photos are stored below `data/`. On Railway, mount persistent storage at `/app/data` and set the paths above. Image OCR extracts text only; it does not automatically verify fixtures. Confirm team names and run `/analyze` yourself.

The model uses a simple Poisson estimate from recent goals. It is not a professional predictive model, does not include injuries or lineups, and does not guarantee a match result or profit. Respect data-provider terms and local laws.

## License

Starter software; adapt as needed. Check the terms of any data provider you use.
