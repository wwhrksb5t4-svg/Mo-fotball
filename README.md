# Mo-football ⚽

Telegram football-analysis bot. It accepts match images, extracts Arabic/English OCR text, saves records, and calculates simple probability estimates from football-data.org results. Estimates are not guaranteed outcomes or profit.

## Railway setup

1. Open your Railway project and select the **bot service**.
2. Go to **Settings → Networking → Public Networking** and choose **Generate Domain**. Railway will display the public `*.up.railway.app` domain there. The code cannot create this domain for you.
3. In **Variables**, set `TELEGRAM_BOT_TOKEN` from @BotFather and `TELEGRAM_WEBHOOK_URL` to `https://YOUR-DOMAIN/webhook` using the domain from step 2.
4. `TELEGRAM_WEBHOOK_SECRET` is optional. If set, use only letters, digits, `_`, and `-`; do not share it.
5. For persistent database storage, add Railway PostgreSQL and reference its `DATABASE_URL` in the bot service. SQLite is the fallback; mount a volume at `/app/data` and set `DATABASE_PATH=/app/data/bot.db`. Mount a volume for image files at `/app/data` and set `PHOTOS_DIR=/app/data/photos`.
6. `FOOTBALL_DATA_TOKEN` is needed only for `/analyze`.
7. Redeploy. `/health` should return `telegram_webhook_ready: true`; then message the bot with `/start`.

This service uses webhooks; do not run a second polling bot with the same token. Never expose bot tokens or database connection URLs.

## Commands

- `/start`, `/help`
- `/analyze PL|Arsenal|Chelsea`
- Send a photo for OCR (review team names manually)

Competition codes: `PL`, `PD`, `BL1`, `SA`, `FL1`.
