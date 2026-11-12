import os
import re
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL", "").strip()
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()
FOOTBALL_DATA_TOKEN = os.getenv("FOOTBALL_DATA_TOKEN", "").strip()
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
DATABASE_PATH = os.getenv("DATABASE_PATH", "/app/data/bot.db").strip()
PHOTOS_DIR = os.getenv("PHOTOS_DIR", "/app/data/photos").strip()
OCR_LANG = os.getenv("OCR_LANG", "eng+ara").strip()


def resolve_webhook_url() -> str:
    value = TELEGRAM_WEBHOOK_URL
    if not value:
        domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
        if domain:
            value = domain if "://" in domain else f"https://{domain}"
        else:
            static_url = os.getenv("RAILWAY_STATIC_URL", "").strip()
            if static_url:
                value = static_url if "://" in static_url else f"https://{static_url}"
        if value and not urlparse(value).path:
            value = value.rstrip("/") + "/webhook"

    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path.rstrip("/") != "/webhook" or parsed.query or parsed.fragment:
        raise RuntimeError(
            "Set TELEGRAM_WEBHOOK_URL to your public Railway HTTPS address ending in /webhook."
        )

    if TELEGRAM_WEBHOOK_SECRET and not re.fullmatch(r"[A-Za-z0-9_-]{1,256}", TELEGRAM_WEBHOOK_SECRET):
        raise RuntimeError("TELEGRAM_WEBHOOK_SECRET must use only letters, numbers, underscores, or hyphens.")
    return value.rstrip("/")
