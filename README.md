# 10-B Aniq Lesson Reminder & Document Vault Bot

A Telegram bot for the 10-B Aniq class that:

1. Sends a full lesson brief every weekday at **08:45** (15 min before the
   09:00 start), always listing all 7 lesson slots and stating exactly when
   the school day ends.
2. Delivers a stored file when a user sends the matching secret code.
3. Lets anyone preview any day's brief on demand with `/check <day>`.

## Files

| File | Purpose |
|---|---|
| `bot.py` | Bot logic: handlers, scheduling, message rendering |
| `config.py` | All editable data — bot token, timetable, secret codes |
| `documents/` | Where the files served by the secret-code vault live |
| `requirements.txt` | Python dependencies |

## Setup

1. **Create the bot** with [@BotFather](https://t.me/BotFather) and copy the token it gives you.

2. **Install dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Set your bot token** as an environment variable (recommended, keeps it
   out of source control):
   ```bash
   export BOT_TOKEN="123456:ABC-your-real-token"
   ```
   Or edit `BOT_TOKEN` directly in `config.py` (not recommended for shared repos).

4. **Add your real documents** into the `documents/` folder, and update the
   `SECRET_CODES` dictionary in `config.py` to map each code to its file:
   ```python
   SECRET_CODES = {
       "ALGEBRA2024": "documents/algebra_notes.pdf",
       "FIZIKA-KEY": "documents/fizika_formulas.pdf",
   }
   ```

5. **Run the bot:**
   ```bash
   python bot.py
   ```

## Usage

- `/start` — subscribes the current chat to the 08:45 Mon–Fri reminder and
  shows a short help message.
- `/stop` — unsubscribes the current chat from reminders.
- `/check <day>` — previews the brief for any day, regardless of today's
  actual date. Valid day codes: `du` (Mon), `se` (Tue), `ch` (Wed),
  `pa` (Thu), `ju` (Fri). Example: `/check ch`.
- Sending a secret code as a plain message (e.g. `ALGEBRA2024`) returns the
  matching file, if one is configured and present on disk.

Only chats that have sent `/start` are stored (in `subscribers.json`,
created automatically) and receive the automatic 08:45 reminder.

## Known data issue to double-check

In the original schedule spec, **Friday (Ju) lesson 6** was listed as
`Informatika | Room: Xursand / Umarbek` — with no separate teacher field and
no actual room number, just what look like two teacher names sitting in the
room slot. In `config.py` this is encoded as:

```python
{"subject": "Informatika", "room": None, "teachers": ["Xursand", "Umarbek"]},
```

The bot will display this as `Room: TBD`. Please confirm the real room
number with the school and update that line.

## Notes on scheduling

The daily reminder uses `python-telegram-bot`'s `JobQueue.run_daily`, which
is itself implemented on top of **APScheduler**'s `AsyncIOScheduler`. Using
the built-in `JobQueue` (rather than instantiating a second, separate
APScheduler instance) avoids event-loop conflicts with the bot's own
polling loop, while still using APScheduler under the hood as specified.
The job time is pinned to the `Asia/Tashkent` timezone (see `TIMEZONE` in
`config.py`), so it will fire at the correct local time regardless of what
timezone the server itself is running in.
