# Mo-football ⚽

Telegram football-analysis bot. It accepts match images, extracts Arabic/English OCR text, saves records, and calculates simple probability estimates from football-data.org results. Estimates are not guaranteed outcomes or profit.

## Railway deployment

1. Deploy this repository with the included Dockerfile and create a public HTTPS domain.
2. Set `TELEGRAM_BOT_TOKEN` to the current token from @BotFather.
3. Set `TELEGRAM_WEBHOOK_URL` to `https://YOUR-DOMAIN/webhook`.
4. Optionally set `TELEGRAM_WEBHOOK_SECRET` to a random string made only of letters, digits, `_`, and `-`.
5. For persistent structured data, add a Railway PostgreSQL service and reference its connection URL as this service's `DATABASE_URL`. The bot creates the tables and indexes on startup. If not set, SQLite is used.
6. Add a Railway Volume mounted at `/app/data` and set `PHOTOS_DIR=/app/data/photos`, so uploaded image files persist. For SQLite persistence also set `DATABASE_PATH=/app/data/bot.db`.
7. `FOOTBALL_DATA_TOKEN` is required only for `/analyze`. `OCR_LANG=eng+ara` uses the OCR language packs installed in the Docker image.
8. Redeploy. Open `/health`; expect `telegram_webhook_ready: true`. Then send `/start` to the bot.

Do not run a second polling bot with the same token; webhook and polling conflict. Never publish bot tokens or database URLs. The service suppresses HTTP client request logs because Telegram API paths contain the bot token.

## Commands

- `/start` and `/help`
- `/analyze PL|Arsenal|Chelsea`
- Send a photo to save it and return extracted text. OCR does not identify a fixture automatically; verify teams and analyze manually.

Supported competition codes: `PL`, `PD`, `BL1`, `SA`, `FL1`.

## Troubleshooting

- No reply: check `/health` says `telegram_webhook_ready: true`; then send `/start` and inspect Railway HTTP access logs for `POST /webhook`.
- No incoming POST: verify the webhook URL is the public Railway domain plus `/webhook`, and confirm you are messaging the bot created by the token configured in the service.
- HTTP 403 on `/webhook`: verify the webhook secret setting; do not share the secret.
- Analysis fails: verify `FOOTBALL_DATA_TOKEN`, competition code, and team names.
