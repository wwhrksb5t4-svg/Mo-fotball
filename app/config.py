import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL")
FOOTBALL_DATA_TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/bot.db")
OCR_LANG = os.getenv("OCR_LANG", "eng")
