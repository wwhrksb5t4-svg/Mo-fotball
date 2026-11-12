from contextlib import asynccontextmanager
import hmac
from urllib.parse import urlparse

from fastapi import FastAPI, Header, HTTPException, Request
from telegram import Update
from telegram.error import InvalidToken

from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_SECRET, TELEGRAM_WEBHOOK_URL
from app.db import init_db
from app.telegram_bot import build_application


def validate_webhook_url(value: str) -> str:
    if not value:
        raise RuntimeError(
            "TELEGRAM_WEBHOOK_URL is missing. In Railway Variables, set it to "
            "https://your-public-domain/webhook, then redeploy."
        )
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path.rstrip("/") != "/webhook" or parsed.query or parsed.fragment:
        raise RuntimeError(
            "TELEGRAM_WEBHOOK_URL must be a public HTTPS URL ending exactly in /webhook."
        )
    return value.rstrip("/")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    webhook_url = validate_webhook_url(TELEGRAM_WEBHOOK_URL)
    telegram_app = build_application()
    initialized = False
    started = False

    try:
        try:
            await telegram_app.initialize()
            initialized = True
        except InvalidToken:
            # Avoid logging the token embedded in python-telegram-bot's exception.
            raise RuntimeError(
                "Telegram rejected TELEGRAM_BOT_TOKEN. Replace it with the current token "
                "from @BotFather in Railway Variables, then redeploy."
            ) from None

        await telegram_app.bot.set_webhook(
            url=webhook_url,
            secret_token=TELEGRAM_WEBHOOK_SECRET or None,
            allowed_updates=Update.ALL_TYPES,
        )
        await telegram_app.start()
        started = True
        app.state.telegram_app = telegram_app
        app.state.webhook_ready = True
        yield
    finally:
        app.state.webhook_ready = False
        if started:
            await telegram_app.stop()
        if initialized:
            await telegram_app.shutdown()


app = FastAPI(title="Mo-football", lifespan=lifespan)


@app.get("/")
@app.get("/health")
async def health(request: Request) -> dict[str, str | bool]:
    ready = bool(getattr(request.app.state, "webhook_ready", False))
    return {
        "status": "ok" if ready else "starting",
        "service": "Mo-football",
        "telegram_webhook_ready": ready,
    }


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

    telegram_app = getattr(request.app.state, "telegram_app", None)
    if telegram_app is None:
        raise HTTPException(status_code=503, detail="Telegram bot is not ready")

    try:
        payload = await request.json()
        update = Update.de_json(payload, telegram_app.bot)
        await telegram_app.process_update(update)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid Telegram update payload") from None
    return {"ok": True}
