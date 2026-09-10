"""
10-B Aniq Lesson Reminder and Document Vault — Telegram bot.

Run with:  python bot.py
Requires:  BOT_TOKEN set as an environment variable (see config.py / README).

Features
--------
1. Secure Document Vault: send a known secret code as a plain text message,
   get the matching file back.
2. Automated Mon-Fri 08:45 daily brief with the full lesson list, including
   an explicit line for lesson 7 even when it's unused, and an explicit
   "school day ends at ..." line.
3. /check <day> diagnostic command to preview any day's brief on demand
   (day codes: du, se, ch, pa, ju).
4. Real-time per-lesson notifications: a message fires the moment each
   lesson ends, announcing the next lesson's subject/room/teacher/start
   time, or "school's out" after the actual last lesson of the day.

Scheduling is done with python-telegram-bot's JobQueue, which is built on
top of APScheduler (AsyncIOScheduler) internally — this avoids manually
wiring a second event loop alongside PTB's own, while still using
APScheduler under the hood as specified.
"""

import json
import logging
import os
from datetime import time as dtime
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


# ---------------------------------------------------------------------------
# Subscriber persistence (which chats should get the 08:45 reminder)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Schedule rendering
# ---------------------------------------------------------------------------

def build_daily_brief(day_code: str) -> str:
    """Render the full lesson brief for a given day code (du/se/ch/pa/ju)."""
    day_code = day_code.lower()
    if day_code not in TIMETABLE:
        valid = ", ".join(DAY_CODES)
        return f"Unknown day code '{day_code}'. Valid codes: {valid}"

    lessons = TIMETABLE[day_code]
    day_name = DAY_NAMES[day_code]

    lines = [f"📅 <b>{day_name} — 10-B Aniq</b>", ""]

    last_active_end = None  # end time of the last real (non-empty) lesson

    for slot in BELL_SCHEDULE:  # always 7 slots, in order
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


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

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


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Checks incoming plain text against the secret-code document vault."""
    text = (update.message.text or "").strip()
    match = SECRET_CODES.get(text) or next(
        (path for code, path in SECRET_CODES.items() if code.lower() == text.lower()),
        None,
    )

    if not match:
        return  # not a recognized code — silently ignore

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


# ---------------------------------------------------------------------------
# Daily reminder job (runs Mon-Fri at REMINDER_HOUR:REMINDER_MINUTE)
# ---------------------------------------------------------------------------

async def send_daily_reminders(context: ContextTypes.DEFAULT_TYPE) -> None:
    weekday = context.job.data["weekday"]  # 0=Mon .. 4=Fri, fixed per job
    day_code = DAY_CODES[weekday]
    brief = build_daily_brief(day_code)

    subscribers = load_subscribers()
    if not subscribers:
        logger.info("Daily reminder triggered but no subscribers yet.")
        return

    for chat_id in subscribers:
        try:
            await context.bot.send_message(chat_id, brief, parse_mode=ParseMode.HTML)
        except Exception as exc:  # noqa: BLE001 - log and keep going for other users
            logger.error("Failed to send reminder to %s: %s", chat_id, exc)


# ---------------------------------------------------------------------------
# Per-lesson job: fires at the end of each lesson, announces what's next
# ---------------------------------------------------------------------------

async def announce_next_lesson(context: ContextTypes.DEFAULT_TYPE) -> None:
    data = context.job.data
    weekday = data["weekday"]
    lesson_index = data["lesson_index"]  # 0-based index of the lesson that just ended
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
        except Exception as exc:  # noqa: BLE001 - log and keep going for other users
            logger.error("Failed to send lesson-end announcement to %s: %s", chat_id, exc)


# ---------------------------------------------------------------------------
# Application setup
# ---------------------------------------------------------------------------

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
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
    )

    # One job per weekday (Mon-Fri) at 08:45 local (Asia/Tashkent) time.
    # JobQueue.run_daily is backed by APScheduler's AsyncIOScheduler.
    reminder_time = _tz_time(f"{REMINDER_HOUR:02d}:{REMINDER_MINUTE:02d}")
    for weekday in range(5):  # 0=Monday .. 4=Friday
        application.job_queue.run_daily(
            send_daily_reminders,
            time=reminder_time,
            days=(weekday,),
            data={"weekday": weekday},
            name=f"daily_reminder_{DAY_CODES[weekday]}",
        )

    # One job per (weekday, lesson) pair, firing at that lesson's END time,
    # for every slot that actually has a lesson scheduled that day. Skips
    # unused slots since no lesson ends there.
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
                days=(weekday,),
                data={"weekday": weekday, "lesson_index": lesson_index},
                name=f"lesson_end_{day_code}_{lesson_index + 1}",
            )

    logger.info("Bot starting (polling)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
