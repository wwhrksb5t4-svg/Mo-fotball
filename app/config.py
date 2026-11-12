import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL", "").strip()
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()
FOOTBALL_DATA_TOKEN = os.getenv("FOOTBALL_DATA_TOKEN", "").strip()
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/bot.db").strip()
OCR_LANG = os.getenv("OCR_LANG", "eng").strip()
