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
- `FOOTBALL_DATA_TOKEN`: API token from [football-data.org](https://www.football-data.org/). Needed for `/analyze`, not for startup.

Never commit `.env` or send tokens in chat.

## Deploy on Railway

1. Deploy this GitHub repository as a Railway service. The included Dockerfile installs Python and Arabic/English Tesseract OCR, then starts Uvicorn on Railway's `$PORT`.
2. Generate a public HTTPS domain for the service.
3. Set `TELEGRAM_BOT_TOKEN` from BotFather and `TELEGRAM_WEBHOOK_URL` to `https://YOUR-DOMAIN/webhook` in the service Variables.
4. Add a Railway Volume mounted at `/app/data` so the SQLite database and uploaded images survive redeployments.
5. Set the variables below and redeploy. Check `/health`; it should return `telegram_webhook_ready: true`, then message the bot with `/start`.

Required Railway variables:

```text
TELEGRAM_BOT_TOKEN=...                 # from BotFather
TELEGRAM_WEBHOOK_URL=https://YOUR-DOMAIN/webhook
FOOTBALL_DATA_TOKEN=...                # needed for match analysis
TELEGRAM_WEBHOOK_SECRET=...             # recommended; random letters/numbers/_/-
DATABASE_PATH=/app/data/bot.db
PHOTOS_DIR=/app/data/photos
OCR_LANG=eng+ara
```

The included Dockerfile provides the start command. If overriding it, use:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

The service validates that the webhook URL is HTTPS and ends in `/webhook`; startup fails with a clear message if it is missing or malformed. If Telegram rejects the token, replace it in Railway Variables with the current BotFather token and redeploy. Never paste secrets into GitHub or chat.

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

Fill in `.env`. Telegram requires a public HTTPS webhook, so local testing needs an HTTPS tunnel; set `TELEGRAM_WEBHOOK_URL` to its public `/webhook` URL. Then run:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

`/health` reports whether webhook startup completed. A local server without a public HTTPS tunnel cannot receive Telegram messages.

## Storage and analysis notes

The default database and photos are stored below `data/`. On Railway, mount persistent storage at `/app/data` and set the paths above. Image OCR extracts text only; it does not automatically verify fixtures. Confirm team names and run `/analyze` yourself.

The model uses a simple Poisson estimate from recent goals. It is not a professional predictive model, does not include injuries or lineups, and does not guarantee a match result or profit. Respect data-provider terms and local laws.
