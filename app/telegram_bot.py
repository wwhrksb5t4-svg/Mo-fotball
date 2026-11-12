import os
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from app.analytical import calculate_probabilities, best_team_match, team_averages
from app.config import FOOTBALL_DATA_TOKEN, OCR_LANG, TELEGRAM_BOT_TOKEN
from app.db import get_connection
from app.football_api import fetch_competition_teams, fetch_team_matches
from app.ocr import read_image_text


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أهلا! هذا بوت تحليل مباريات كرة القدم.\n\n"
        "استخدم الأمر:\n"
        "/analyze PL|Arsenal|Chelsea\n\n"
        "أو أرسل صورة للمباراة لاحتفاظك بالنص المستخرج منها."
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "استخدام البوت:\n"
        "- /start\n"
        "- /help\n"
        "- /analyze PL|Arsenal|Chelsea\n\n"
        "الملاحظات:\n"
        "- هذا تحليل إحصائي مبسط\n"
        "- لا يضمن الربح أو النتيجة\n"
        "- يمكن للأوامر قبول أسماء فرق حسب التطابق الواسع."
    )


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.photo:
        return

    photo = update.message.photo[-1]
    user_id = update.effective_user.id if update.effective_user else 0
    file_name = f"{user_id}_{photo.file_unique_id}.jpg"
    photo_dir = os.path.join("data", "photos")
    os.makedirs(photo_dir, exist_ok=True)
    file_path = os.path.join(photo_dir, file_name)

    telegram_file = await photo.get_file()
    await telegram_file.download_to_drive(custom_path=file_path)

    try:
        ocr_text = read_image_text(file_path, OCR_LANG)
    except Exception as exc:
        ocr_text = f"Failed to OCR: {exc}"

    conn = get_connection()
    conn.execute(
        "INSERT INTO photo_records (user_id, file_path, ocr_text, created_at) VALUES (?, ?, ?, ?)",
        (user_id, file_path, ocr_text, utc_now()),
    )
    conn.commit()
    conn.close()

    preview = ocr_text[:1500]
    await update.message.reply_text(f"تم حفظ الصورة.\n\nالنص المستخرج:\n{preview}")


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not FOOTBALL_DATA_TOKEN:
        await update.message.reply_text("لم يتم ضبط FOOTBALL_DATA_TOKEN في ملف .env")
        return

    raw = " ".join(context.args)
    parts = [part.strip() for part in raw.split("|")]

    if len(parts) != 3:
        await update.message.reply_text("الصيغة المطلوبة:\n/analyze PL|Arsenal|Chelsea")
        return

    competition, home_query, away_query = parts
    competition = competition.strip().upper()

    try:
        teams = await fetch_competition_teams(competition, FOOTBALL_DATA_TOKEN)
        home_team = best_team_match(home_query, teams)
        away_team = best_team_match(away_query, teams)

        home_matches = await fetch_team_matches(home_team["id"], FOOTBALL_DATA_TOKEN)
        away_matches = await fetch_team_matches(away_team["id"], FOOTBALL_DATA_TOKEN)

        home_stats = team_averages(home_team["id"], home_matches)
        away_stats = team_averages(away_team["id"], away_matches)

        home_xg = (home_stats[0] + away_stats[1]) / 2
        away_xg = (away_stats[0] + home_stats[1]) / 2
        probs = calculate_probabilities(home_xg, away_xg)

        report = (
            f"تحليل مباراة — {competition}\n"
            f"{home_team['name']} × {away_team['name']}\n\n"
            f"فوز المضيف: {probs['home']:.0%}\n"
            f"تعادل: {probs['draw']:.0%}\n"
            f"فوز الضيف: {probs['away']:.0%}\n"
            f"أكثر من 2.5: {probs['over25']:.0%}\n\n"
            f"القيمة المتوقعة: {home_xg:.2f} / {away_xg:.2f}\n\n"
            "ملاحظة: هذا تحليل إحصائي مبسط ولا يضمن الربح أو النتيجة."
        )

        conn = get_connection()
        conn.execute(
            "INSERT INTO analysis_records (user_id, competition, home_team, away_team, report, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (update.effective_user.id, competition, home_team["name"], away_team["name"], report, utc_now()),
        )
        conn.commit()
        conn.close()

        await update.message.reply_text(report)

    except Exception as exc:
        await update.message.reply_text(f"تعذر إتمام التحليل: {exc}\n\nجرّب صيغة مثل: /analyze PL|Arsenal|Chelsea")


def build_application() -> Application:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing. Check your .env file.")

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    return application
