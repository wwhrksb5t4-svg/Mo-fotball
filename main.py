from contextlib import asynccontextmanager
import hmac

from fastapi import FastAPI, Header, HTTPException, Request
from telegram import Update

from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_SECRET, TELEGRAM_WEBHOOK_URL
from app.db import init_db
from app.telegram_bot import build_application


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    telegram_app = build_application()
    await telegram_app.initialize()
    if TELEGRAM_WEBHOOK_URL:
        await telegram_app.bot.set_webhook(
            url=TELEGRAM_WEBHOOK_URL,
            secret_token=TELEGRAM_WEBHOOK_SECRET or None,
            allowed_updates=Update.ALL_TYPES,
        )
    await telegram_app.start()
    app.state.telegram_app = telegram_app
    try:
        yield
    finally:
        await telegram_app.stop()
        await telegram_app.shutdown()


app = FastAPI(title="Mo-football", lifespan=lifespan)


@app.get("/")
@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "Mo-football"}


@app.post("/webhook")
async def webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if not TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=503, detail="Bot token is not configured")
    if TELEGRAM_WEBHOOK_SECRET and not hmac.compare_digest(
        x_telegram_bot_api_secret_token or "", TELEGRAM_WEBHOOK_SECRET
    ):
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    telegram_app = request.app.state.telegram_app
    payload = await request.json()
    update = Update.de_json(payload, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}
