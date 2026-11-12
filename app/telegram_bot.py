import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from app.analytics import best_team_match, calculate_probabilities, team_averages
from app.config import DATABASE_PATH, FOOTBALL_DATA_TOKEN, OCR_LANG, TELEGRAM_BOT_TOKEN
from app.db import get_connection
from app.football_api import fetch_competition_teams, fetch_team_matches
from app.ocr import read_image_text

SUPPORTED_COMPETITIONS = {"PL", "PD", "BL1", "SA", "FL1"}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _photo_directory() -> Path:
    directory = Path(os.getenv("PHOTOS_DIR", str(Path(DATABASE_PATH).parent / "photos")))
    directory.mkdir(parents=True, exist_ok=True)
    return directory


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "أهلًا بك في Mo-football ⚽\n\n"
        "أرسل صورة لاستخراج النص وحفظها، أو حلّل مباراة بهذا الأمر:\n"
        "/analyze PL|Arsenal|Chelsea\n\n"
        "التحليل إحصائي مبسط ولا يضمن نتيجة أو ربحًا."
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "الأوامر:\n"
        "/start — بدء الاستخدام\n"
        "/help — المساعدة\n"
        "/analyze PL|Arsenal|Chelsea — تحليل مباراة\n\n"
        "رموز البطولات المدعومة: PL, PD, BL1, SA, FL1.\n"
        "راجع أسماء الفرق المستخرجة من الصورة يدويًا. التوقعات احتمالية وليست ضمانًا."
    )


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message or not message.photo:
        return

    photo = message.photo[-1]
    user_id = update.effective_user.id if update.effective_user else 0
    file_path = _photo_directory() / f"{user_id}_{photo.file_unique_id}.jpg"
    telegram_file = await photo.get_file()
    await telegram_file.download_to_drive(custom_path=str(file_path))

    try:
        ocr_text = await asyncio.to_thread(read_image_text, str(file_path), OCR_LANG)
        if not ocr_text:
            ocr_text = "لم يتم العثور على نص واضح في الصورة."
    except Exception as exc:
        ocr_text = f"تعذر استخراج النص. تحقق من تثبيت Tesseract واللغة المطلوبة. ({exc})"

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO photo_records (user_id, file_path, ocr_text, created_at) VALUES (?, ?, ?, ?)",
            (user_id, str(file_path), ocr_text, utc_now()),
        )

    await message.reply_text(
        f"تم حفظ الصورة. النص المستخرج:\n\n{ocr_text[:2500]}\n\n"
        "إذا كانت الصورة لمباراة، أكد أسماء الفرق يدويًا ثم استخدم /analyze."
    )


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not FOOTBALL_DATA_TOKEN:
        await message.reply_text("مصدر بيانات المباريات غير مضبوط. أضف FOOTBALL_DATA_TOKEN في إعدادات الخدمة.")
        return

    raw = " ".join(context.args)
    parts = [part.strip() for part in raw.split("|")]
    if len(parts) != 3:
        await message.reply_text("الصيغة المطلوبة:\n/analyze PL|Arsenal|Chelsea")
        return

    competition, home_query, away_query = parts
    competition = competition.upper()
    if competition not in SUPPORTED_COMPETITIONS:
        await message.reply_text("رمز بطولة غير مدعوم. استخدم PL أو PD أو BL1 أو SA أو FL1.")
        return

    await message.reply_text("جاري جلب البيانات وإعداد التحليل…")
    try:
        teams = await fetch_competition_teams(competition, FOOTBALL_DATA_TOKEN)
        home_team = best_team_match(home_query, teams)
        away_team = best_team_match(away_query, teams)
        if home_team["id"] == away_team["id"]:
            raise ValueError("تمت مطابقة الاسمين مع الفريق نفسه؛ راجع الإدخال.")

        home_matches, away_matches = await asyncio.gather(
            fetch_team_matches(home_team["id"], FOOTBALL_DATA_TOKEN),
            fetch_team_matches(away_team["id"], FOOTBALL_DATA_TOKEN),
        )
        home_stats = team_averages(home_team["id"], home_matches)
        away_stats = team_averages(away_team["id"], away_matches)
        home_xg = (home_stats[0] + away_stats[1]) / 2
        away_xg = (away_stats[0] + home_stats[1]) / 2
        probabilities = calculate_probabilities(home_xg, away_xg)

        report = (
            f"تحليل مباراة — {competition}\n{home_team['name']} × {away_team['name']}\n\n"
            f"فوز المضيف: {probabilities['home']:.0%}\n"
            f"تعادل: {probabilities['draw']:.0%}\n"
            f"فوز الضيف: {probabilities['away']:.0%}\n"
            f"أكثر من 2.5 هدف: {probabilities['over25']:.0%}\n\n"
            f"مؤشر الأهداف المبسط: {home_xg:.2f} — {away_xg:.2f}\n"
            f"العينة: {home_stats[2]} مباراة للمضيف و{away_stats[2]} مباراة للضيف.\n"
            "المصدر: football-data.org.\n\n"
            "هذا تقدير إحصائي مبسط، لا يتضمن الإصابات والتشكيلات، ولا يضمن النتيجة أو الربح."
        )
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO analysis_records (user_id, competition, home_team, away_team, report, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (update.effective_user.id, competition, home_team["name"], away_team["name"], report, utc_now()),
            )
        await message.reply_text(report)
    except Exception as exc:
        await message.reply_text(
            f"تعذر إتمام التحليل: {exc}\nتحقق من رمز البطولة وتهجئة الفرق ومفتاح API."
        )


def build_application() -> Application:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured.")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    return application
