from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application

from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_URL
from app.telegram_bot import build_application

app = FastAPI(title="Mo-football Bot")
application = build_application()

@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}

@app.post("/webhook")
async def webhook(request: Request):
    if not TELEGRAM_BOT_TOKEN:
        return {"status": "bot token not configured"}

    payload = await request.json()
    update = Update.de_json(payload, application.bot)
    await application.process_update(update)
    return {"ok": True}

@app.on_event("startup")
async def startup_event():
    if TELEGRAM_BOT_TOKEN and TELEGRAM_WEBHOOK_URL:
        await application.bot.set_webhook(url=TELEGRAM_WEBHOOK_URL)
        print(f"Webhook set to: {TELEGRAM_WEBHOOK_URL}")
    else:
        print("No Telegram webhook URL configured. Set TELEGRAM_WEBHOOK_URL to enable webhook updates.")

