"""
10-B Aniq Lesson Reminder and Document Vault — Telegram bot.

Run with:  python bot.py
Requires:  BOT_TOKEN set as an environment variable (see config.py / README).
"""

import json
import logging
import os
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import (
    BELL_SCHEDULE,
    BOT_TOKEN,
    DAY_CODES,
    DAY_NAMES,
    REMINDER_HOUR,
    REMINDER_MINUTE,
    SECRET_CODES,
    SUBSCRIBERS_FILE,
    TIMETABLE,
    TIMEZONE,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("aniq10b_bot")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _tz_time(hhmm: str) -> dtime:
    """Parse an 'HH:MM' string into a tz-aware time in TIMEZONE."""
    hour, minute = map(int, hhmm.split(":"))
    return dtime(hour=hour, minute=minute, tzinfo=ZoneInfo(TIMEZONE))


def load_subscribers() -> set:
    if not os.path.exists(SUBSCRIBERS_FILE):
        return set()
    try:
        with open(SUBSCRIBERS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read subscribers file (%s), starting empty.", exc)
        return set()


def save_subscribers(subscribers: set) -> None:
    with open(SUBSCRIBERS_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(subscribers), f)


def build_daily_brief(day_code: str) -> str:
    """Render the full lesson brief for a given day code (du/se/ch/pa/ju)."""
    day_code = day_code.lower()
    if day_code not in TIMETABLE:
        valid = ", ".join(DAY_CODES)
        return f"Unknown day code '{day_code}'. Valid codes: {valid}"

    lessons = TIMETABLE[day_code]
    day_name = DAY_NAMES[day_code]

    lines = [f"📅 <b>{day_name} — 10-B Aniq</b>", ""]
    last_active_end = None

    for slot in BELL_SCHEDULE:
        idx = slot["lesson"] - 1
        entry = lessons[idx] if idx < len(lessons) else None
        time_range = f"{slot['start']}–{slot['end']}"

        if entry is None:
            lines.append(f"{slot['lesson']}. <i>{time_range} — (bo'sh / unused)</i>")
            continue

        last_active_end = slot["end"]
        teachers = ", ".join(entry["teachers"])
        room = entry["room"] if entry["room"] else "TBD"
        lines.append(
            f"{slot['lesson']}. {time_range} — <b>{entry['subject']}</b>\n"
            f"    🏫 Room: {room}   👤 {teachers}"
        )

    lines.append("")
    if last_active_end:
        lines.append(f"🔔 School day finishes at <b>{last_active_end}</b>.")
    else:
        lines.append("🔔 No lessons scheduled for this day.")

    return "\n".join(lines)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    subscribers = load_subscribers()
    if chat_id not in subscribers:
        subscribers.add(chat_id)
        save_subscribers(subscribers)

    await update.message.reply_text(
        "Salom! 👋 I'll send the 10-B Aniq lesson brief every weekday at "
        f"{REMINDER_HOUR:02d}:{REMINDER_MINUTE:02d}.\n\n"
        "Commands:\n"
        "  /check <du|se|ch|pa|ju> — preview any day's schedule\n"
        "  /lesson [date|day] [HH:MM] — check what lesson is currently active\n"
        "  /stop — stop receiving daily reminders\n\n"
        "You can also send a secret code as a plain message to receive a "
        "stored document."
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    subscribers = load_subscribers()
    if chat_id in subscribers:
        subscribers.discard(chat_id)
        save_subscribers(subscribers)
        await update.message.reply_text("You won't receive daily reminders anymore.")
    else:
        await update.message.reply_text("You weren't subscribed.")


async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        valid = ", ".join(DAY_CODES)
        await update.message.reply_text(f"Usage: /check <day>\nValid codes: {valid}")
        return

    day_code = context.args[0].lower()
    brief = build_daily_brief(day_code)
    await update.message.reply_text(brief, parse_mode=ParseMode.HTML)


async def lesson_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Checks active lesson status for a specific date (e.g. 24.09.2026) or day name, 
    and optional hour (e.g. 10:30). Defaults to current date and time.
    """
    now_local = datetime.now(ZoneInfo(TIMEZONE))
    target_date = now_local.date()
    target_time = now_local.time()
    
    args = context.args
    day_code = None
    
    if args:
        first_arg = args[0].lower()
        try:
            parsed_dt = datetime.strptime(first_arg, "%d.%m.%Y")
            target_date = parsed_dt.date()
            weekday = target_date.weekday()
            if weekday > 4:
                await update.message.reply_text(f"📅 {target_date.strftime('%d.%m.%Y')} is a weekend! No lessons scheduled.")
                return
            day_code = DAY_CODES[weekday]
        except ValueError:
            day_map = {
                "du": "du", "dushanba": "du", "monday": "du", "mon": "du",
                "se": "se", "seshanba": "se", "tuesday": "se", "tue": "se",
                "ch": "ch", "chorshanba": "ch", "wednesday": "ch", "wed": "ch",
                "pa": "pa", "payshanba": "pa", "thursday": "pa", "thu": "pa",
                "ju": "ju", "juma": "ju", "friday": "ju", "fri": "ju",
            }
            if first_arg in day_map:
                day_code = day_map[first_arg]
            else:
                await update.message.reply_text(
                    "Invalid format! Usage examples:\n"
                    "  /lesson\n"
                    "  /lesson 24.09.2026 10:30\n"
                    "  /lesson friday 11:00"
                )
                return
        
        if len(args) > 1:
            try:
                th, tm = map(int, args[1].split(":"))
                target_time = dtime(hour=th, minute=tm, tzinfo=ZoneInfo(TIMEZONE))
            except ValueError:
                await update.message.reply_text("Invalid time format! Use HH:MM (e.g. 10:30).")
                return
    else:
        weekday = now_local.weekday()
        if weekday > 4:
            await update.message.reply_text("📅 Today is a weekend! No lessons scheduled.")
            return
        day_code = DAY_CODES[weekday]

    if not day_code or day_code not in TIMETABLE:
        await update.message.reply_text("No timetable found for this day.")
        return

    lessons = TIMETABLE[day_code]
    day_name = DAY_NAMES[day_code]
    target_mins = target_time.hour * 60 + target_time.minute
    
    status_msg = f"🔍 <b>Status for {day_name}</b> (at {target_time.strftime('%H:%M')}):\n\n"
    active_found = False
    
    for slot in BELL_SCHEDULE:
        idx = slot["lesson"] - 1
        entry = lessons[idx] if idx < len(lessons) else None
        
        sh, sm = map(int, slot["start"].split(":"))
        eh, em = map(int, slot["end"].split(":"))
        start_mins = sh * 60 + sm
        end_mins = eh * 60 + em
        
        if start_mins <= target_mins <= end_mins:
            active_found = True
            if entry is None:
                status_msg += f"⏸️ Currently in <b>Lesson {slot['lesson']}</b> ({slot['start']}–{slot['end']}): <i>(bo'sh / unused slot)</i>"
            else:
                teachers = ", ".join(entry["teachers"])
                room = entry["room"] if entry["room"] else "TBD"
                status_msg += (
                    f"📚 Currently in <b>Lesson {slot['lesson']}</b> ({slot['start']}–{slot['end']})\n"
                    f"Subject: <b>{entry['subject']}</b>\n"
                    f"🏫 Room: {room}   👤 {teachers}"
                )
            break
        elif target_mins < start_mins:
            active_found = True
            if slot["lesson"] == 1:
                status_msg += f"⏳ School hasn't started yet. First lesson starts at {slot['start']}."
            else:
                prev_slot = BELL_SCHEDULE[idx - 1]
                status_msg += f"☕ Currently on a break (between Lesson {prev_slot['lesson']} and Lesson {slot['lesson']}). Next up: <b>{entry['subject'] if entry else 'Unused slot'}</b> at {slot['start']}."
            break
    
    if not active_found:
        last_slot = BELL_SCHEDULE[-1]
        last_end_mins = int(last_slot["end"].split(":")[0]) * 60 + int(last_slot["end"].split(":")[1])
        if target_mins > last_end_mins:
            status_msg += "🏁 School day has already finished!"
        else:
            status_msg += "ℹ️ Outside normal school hours."

    await update.message.reply_text(status_msg, parse_mode=ParseMode.HTML)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.message.text or "").strip()
    match = SECRET_CODES.get(text) or next(
        (path for code, path in SECRET_CODES.items() if code.lower() == text.lower()),
        None,
    )

    if not match:
        return

    full_path = match if os.path.isabs(match) else os.path.join(BASE_DIR, match)
    if not os.path.exists(full_path):
        await update.message.reply_text(
            "That code is valid, but the file isn't on the server yet. "
            "Please contact the bot admin."
        )
        logger.warning("Secret code matched but file missing: %s", full_path)
        return

    with open(full_path, "rb") as doc:
        await update.message.reply_document(document=doc)


async def send_daily_reminders(context: ContextTypes.DEFAULT_TYPE) -> None:
    now_local = datetime.now(ZoneInfo(TIMEZONE))
    weekday = now_local.weekday()
    
    if weekday > 4:
        return

    day_code = DAY_CODES[weekday]
    brief = build_daily_brief(day_code)

    subscribers = load_subscribers()
    if not subscribers:
        logger.info("Daily reminder triggered but no subscribers yet.")
        return

    for chat_id in subscribers:
        try:
            await context.bot.send_message(chat_id, brief, parse_mode=ParseMode.HTML)
        except Exception as exc:
            logger.error("Failed to send reminder to %s: %s", chat_id, exc)


async def announce_next_lesson(context: ContextTypes.DEFAULT_TYPE) -> None:
    now_local = datetime.now(ZoneInfo(TIMEZONE))
    weekday = now_local.weekday()
    
    if weekday > 4:
        return

    data = context.job.data
    lesson_index = data["lesson_index"]
    day_code = DAY_CODES[weekday]
    lessons = TIMETABLE[day_code]

    subscribers = load_subscribers()
    if not subscribers:
        return

    next_index = lesson_index + 1
    next_entry = lessons[next_index] if next_index < len(lessons) else None

    if next_entry is None:
        text = "🏁 That was the last lesson — school's out for today!"
    else:
        next_slot = BELL_SCHEDULE[next_index]
        teachers = ", ".join(next_entry["teachers"])
        room = next_entry["room"] if next_entry["room"] else "TBD"
        text = (
            f"⏰ Lesson {lesson_index + 1} has finished.\n"
            f"Next up — Lesson {next_index + 1}: <b>{next_entry['subject']}</b>\n"
            f"🏫 Room: {room}   👤 {teachers}\n"
            f"Starts at {next_slot['start']}"
        )

    for chat_id in subscribers:
        try:
            await context.bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)
        except Exception as exc:
            logger.error("Failed to send lesson-end announcement to %s: %s", chat_id, exc)


def main() -> None:
    if not BOT_TOKEN or BOT_TOKEN == "PUT_YOUR_BOT_TOKEN_HERE":
        raise SystemExit(
            "BOT_TOKEN is not set. Export it as an environment variable "
            "or edit config.py before running the bot."
        )

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("check", check_command))
    application.add_handler(CommandHandler("lesson", lesson_status_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
    )

    reminder_time = _tz_time(f"{REMINDER_HOUR:02d}:{REMINDER_MINUTE:02d}")
    
    application.job_queue.run_daily(
        send_daily_reminders,
        time=reminder_time,
        name="daily_reminder",
    )

    for weekday in range(5):
        day_code = DAY_CODES[weekday]
        lessons = TIMETABLE[day_code]
        for lesson_index, entry in enumerate(lessons):
            if entry is None:
                continue
            slot = BELL_SCHEDULE[lesson_index]
            end_time = _tz_time(slot["end"])
            application.job_queue.run_daily(
                announce_next_lesson,
                time=end_time,
                data={"lesson_index": lesson_index},
                name=f"lesson_end_{day_code}_{lesson_index + 1}",
            )

    logger.info("Bot starting (polling)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()