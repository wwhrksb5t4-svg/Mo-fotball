import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from app.analytics import best_team_match, calculate_probabilities, team_averages
from app.config import DATABASE_PATH, FOOTBALL_DATA_TOKEN, OCR_LANG, PHOTOS_DIR, TELEGRAM_BOT_TOKEN
from app.db import get_connection
from app.football_api import fetch_competition_teams, fetch_team_matches
from app.ocr import read_image_text

logger = logging.getLogger("mo_football.bot")
SUPPORTED_COMPETITIONS = {"PL", "PD", "BL1", "SA", "FL1"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def photo_directory() -> Path:
    path = Path(PHOTOS_DIR or str(Path(DATABASE_PATH).parent / "photos"))
    path.mkdir(parents=True, exist_ok=True)
    return path


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_message:
        await update.effective_message.reply_text(
            "أهلًا بك في Mo-football ⚽\n\n"
            "أرسل صورة لاستخراج النص وحفظها، أو حلّل مباراة بهذا الأمر:\n"
            "/analyze PL|Arsenal|Chelsea\n\n"
            "التحليل إحصائي مبسط ولا يضمن نتيجة أو ربحًا."
        )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_message:
        await update.effective_message.reply_text(
            "الأوامر:\n/start — بدء الاستخدام\n/help — المساعدة\n"
            "/analyze PL|Arsenal|Chelsea — تحليل مباراة\n\n"
            "البطولات: PL, PD, BL1, SA, FL1. التحليل احتمالي وليس ضمانًا."
        )


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message or not message.photo:
        return
    photo = message.photo[-1]
    user_id = update.effective_user.id if update.effective_user else 0
    path = photo_directory() / f"{user_id}_{photo.file_unique_id}.jpg"
    remote_file = await photo.get_file()
    await remote_file.download_to_drive(custom_path=str(path))

    try:
        text = await asyncio.to_thread(read_image_text, str(path), OCR_LANG)
        if not text:
            text = "لم يتم العثور على نص واضح في الصورة."
    except Exception:
        logger.exception("Image OCR failed")
        text = "تعذر استخراج النص. تحقق من ملفات لغة Tesseract المثبتة."

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO photo_records (user_id, file_path, ocr_text, created_at) VALUES (?, ?, ?, ?)",
            (user_id, str(path), text, utc_now()),
        )
    await message.reply_text(f"تم حفظ الصورة. النص المستخرج:\n\n{text[:2500]}")


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message:
        return
    if not FOOTBALL_DATA_TOKEN:
        await message.reply_text("التحليل غير متاح بعد: أضف FOOTBALL_DATA_TOKEN في Railway Variables.")
        return

    parts = [part.strip() for part in " ".join(context.args).split("|")]
    if len(parts) != 3:
        await message.reply_text("الصيغة المطلوبة: /analyze PL|Arsenal|Chelsea")
        return
    competition, home_query, away_query = parts
    competition = competition.upper()
    if competition not in SUPPORTED_COMPETITIONS:
        await message.reply_text("البطولات المدعومة: PL, PD, BL1, SA, FL1.")
        return

    await message.reply_text("جاري تحليل المباراة…")
    try:
        teams = await fetch_competition_teams(competition, FOOTBALL_DATA_TOKEN)
        home = best_team_match(home_query, teams)
        away = best_team_match(away_query, teams)
        if home["id"] == away["id"]:
            raise ValueError("تمت مطابقة الاسمين مع الفريق نفسه؛ راجع الإدخال.")
        home_matches, away_matches = await asyncio.gather(
            fetch_team_matches(home["id"], FOOTBALL_DATA_TOKEN),
            fetch_team_matches(away["id"], FOOTBALL_DATA_TOKEN),
        )
        home_stats = team_averages(home["id"], home_matches)
        away_stats = team_averages(away["id"], away_matches)
        home_xg = (home_stats[0] + away_stats[1]) / 2
        away_xg = (away_stats[0] + home_stats[1]) / 2
        probs = calculate_probabilities(home_xg, away_xg)
        report = (
            f"تحليل — {competition}\n{home['name']} × {away['name']}\n\n"
            f"فوز المضيف: {probs['home']:.0%}\nتعادل: {probs['draw']:.0%}\n"
            f"فوز الضيف: {probs['away']:.0%}\nأكثر من 2.5 هدف: {probs['over25']:.0%}\n\n"
            f"مؤشر الأهداف: {home_xg:.2f} — {away_xg:.2f}\n"
            "المصدر: football-data.org. تقدير مبسط لا يضمن النتيجة أو الربح."
        )
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO analysis_records (user_id, competition, home_team, away_team, report, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (update.effective_user.id, competition, home["name"], away["name"], report, utc_now()),
            )
        await message.reply_text(report)
    except Exception:
        logger.exception("Match analysis failed")
        await message.reply_text("تعذر التحليل. تحقق من مفتاح مزود البيانات، رمز البطولة، وأسماء الفريقين.")


def build_application() -> Application:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured in Railway Variables.")
    if "your_" in TELEGRAM_BOT_TOKEN.lower() or TELEGRAM_BOT_TOKEN.lower() in {"replace_me", "changeme"}:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is still a placeholder; replace it with the BotFather token.")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    return application
