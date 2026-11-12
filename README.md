# Mo-football ⚽

Telegram bot for football match analysis. Accepts match images, extracts Arabic/English OCR text, saves records, and reports simple probability estimates from football-data.org historical results.

## Important
The output is statistical and uncertain, not a guaranteed prediction or profit. Current estimates do not account for injuries, confirmed lineups, or bookmaker prices.

## Setup on Railway

1. Deploy this repository as a Railway service using the included Dockerfile.
2. Generate a public HTTPS domain in the service's Networking settings.
3. Set `TELEGRAM_BOT_TOKEN` to the real token from @BotFather.
4. Set `TELEGRAM_WEBHOOK_URL` to `https://YOUR-PUBLIC-DOMAIN/webhook`. Alternatively, enable Railway's public domain variable `RAILWAY_PUBLIC_DOMAIN`; the app will construct the `/webhook` endpoint automatically.
5. Set `TELEGRAM_WEBHOOK_SECRET` to a random 1-256 character string containing only letters, numbers, `_` or `-`. It must be identical in the service variable throughout deployment. You may leave it blank if you do not need the extra check.
6. For durable storage, add a Railway PostgreSQL service and reference its connection URL in the bot service's `DATABASE_URL` variable (Railway variable reference to Postgres `DATABASE_URL`). The app creates its tables and indexes on startup. If not configured, it uses SQLite; mount a Railway Volume at `/app/data` and set `DATABASE_PATH=/app/data/bot.db`.
7. Mount a Railway Volume at `/app/data` for uploaded image files, and set `PHOTOS_DIR=/app/data/photos`. PostgreSQL stores image paths/OCR records; images themselves are stored on the volume.
8. Redeploy. Visit `/health`; expect `telegram_webhook_ready: true`. Then send `/start` to the bot.

Required/recommended Railway variables:

```text
TELEGRAM_BOT_TOKEN=...                 # required
TELEGRAM_WEBHOOK_URL=https://DOMAIN/webhook  # required unless Railway public domain is enabled
TELEGRAM_WEBHOOK_SECRET=...            # optional but recommended
FOOTBALL_DATA_TOKEN=...                # needed only for /analyze
DATABASE_URL=${{Postgres.DATABASE_URL}} # recommended; add Railway PostgreSQL first
DATABASE_PATH=/app/data/bot.db         # SQLite fallback
PHOTOS_DIR=/app/data/photos
OCR_LANG=eng+ara
```

The included Dockerfile installs Tesseract English and Arabic language data and starts Uvicorn on Railway's `$PORT`. Do not add a competing polling process: the app uses Telegram webhooks.

## Bot usage

- `/start` — greeting
- `/help` — usage information
- `/analyze PL|Arsenal|Chelsea` — request match analysis; requires a valid `FOOTBALL_DATA_TOKEN`
- Send a photo — save it and return extracted text. OCR does not identify/verify fixtures automatically.

Supported competition codes: `PL`, `PD`, `BL1`, `SA`, `FL1`.

## Diagnose no response

- Check `/health`; `telegram_webhook_ready` must be `true`.
- If it stays false or the deployment restarts, inspect Railway logs for webhook URL, credential, or database connection errors.
- Ensure the URL is public HTTPS and ends in `/webhook`.
- If a webhook secret is set, do not change it between app configuration and Telegram webhook registration; this app registers the configured value on startup.
- After deploy, send `/start` and inspect logs for `Mo-football webhook configured and ready`.
- Never post bot tokens, database URLs, or API keys in chat or commit them to GitHub.

## Local run

Requires Python 3.11+, Tesseract with `eng` and `ara` language packs, and a public HTTPS tunnel for Telegram webhook delivery.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in credentials and run `uvicorn main:app --host 0.0.0.0 --port 8000`. Configure the tunnel's public HTTPS `/webhook` URL in `TELEGRAM_WEBHOOK_URL`.
