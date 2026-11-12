from contextlib import asynccontextmanager
import hmac
import logging

from fastapi import FastAPI, Header, HTTPException, Request
from telegram import Update
from telegram.error import InvalidToken

from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_SECRET, resolve_webhook_url
from app.db import init_db
from app.telegram_bot import build_application

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mo_football")


async def telegram_error_handler(update: object, context) -> None:
    # Do not log request payloads or credentials; only the exception details.
    logger.error("Telegram update handler failed", exc_info=context.error)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    webhook_url = resolve_webhook_url()
    telegram_app = build_application()
    initialized = started = False

    try:
        try:
            await telegram_app.initialize()
            initialized = True
        except InvalidToken:
            raise RuntimeError(
                "Telegram rejected TELEGRAM_BOT_TOKEN. Replace it with the current token "
                "from @BotFather in Railway Variables, then redeploy."
            ) from None

        telegram_app.add_error_handler(telegram_error_handler)
        await telegram_app.bot.set_webhook(
            url=webhook_url,
            secret_token=TELEGRAM_WEBHOOK_SECRET or None,
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=False,
        )
        webhook_info = await telegram_app.bot.get_webhook_info()
        if webhook_info.url != webhook_url:
            raise RuntimeError("Telegram did not confirm the configured webhook URL.")

        await telegram_app.start()
        started = True
        app.state.telegram_app = telegram_app
        app.state.webhook_ready = True
        logger.info("Mo-football webhook configured and ready")
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
