"""
Configuration and static data for the 10-B Aniq Lesson Reminder & Document
Vault bot.

Edit the values in this file to match your real bot token, secret codes,
and (if the schedule ever changes) the timetable itself.
"""

import os

# ---------------------------------------------------------------------------
# Bot credentials / environment
# ---------------------------------------------------------------------------

# Prefer setting this as an environment variable (e.g. in a .env file loaded
# by bot.py) rather than hardcoding your real token here.
BOT_TOKEN = os.environ.get("BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")

# IANA timezone name used for the daily 08:45 reminder job.
TIMEZONE = "Asia/Tashkent"

# Where subscriber chat_ids are persisted between restarts.
SUBSCRIBERS_FILE = os.path.join(os.path.dirname(__file__), "subscribers.json")

# ---------------------------------------------------------------------------
# Secure Document Vault
# ---------------------------------------------------------------------------
# Maps a secret code (as typed by the user, case-insensitive) to a local
# file path. When a user sends the exact code as a plain text message, the
# bot replies with the corresponding file.
#
# Paths are resolved relative to this file's directory unless you give an
# absolute path. Put your real files in the documents/ folder and update
# the codes below.
SECRET_CODES = {
    "ALGEBRA2024": "documents/algebra_notes.pdf",
    "FIZIKA-KEY": "documents/fizika_formulas.pdf",
    "vocab": "documents/nnt.pdf",
    "rasp": "documents/rasp.jpg",
    "myielts": "documents/myielts.jpg",
    "mycefr": "documents/mycefr.jpg",
}

# ---------------------------------------------------------------------------
# Daily Bell Schedule
# ---------------------------------------------------------------------------
# Index 0 == Lesson 1, ... Index 6 == Lesson 7.
# "break_after" is a human-readable label for what happens after this
# lesson (a short break, lunch, or end of day) — used only for display.
BELL_SCHEDULE = [
    {"lesson": 1, "start": "09:00", "end": "09:45", "break_after": "5 min break"},
    {"lesson": 2, "start": "09:50", "end": "10:35", "break_after": "5 min break"},
    {"lesson": 3, "start": "10:40", "end": "11:25", "break_after": "5 min break"},
    {"lesson": 4, "start": "11:30", "end": "12:15", "break_after": "30 min lunch break"},
    {"lesson": 5, "start": "12:45", "end": "13:30", "break_after": "5 min break"},
    {"lesson": 6, "start": "13:35", "end": "14:20", "break_after": "5 min break"},
    {"lesson": 7, "start": "14:25", "end": "15:10", "break_after": "End of school day"},
]

# Reminder is sent 15 minutes before the 09:00 start time.
REMINDER_HOUR = 8
REMINDER_MINUTE = 45

# ---------------------------------------------------------------------------
# Weekly Timetable Data (10-B Aniq)
# ---------------------------------------------------------------------------
# Day codes, in weekday order (Monday=0 .. Friday=4), matching /check <day>.
DAY_CODES = ["du", "se", "ch", "pa", "ju"]

DAY_NAMES = {
    "du": "Dushanba (Monday)",
    "se": "Seshanba (Tuesday)",
    "ch": "Chorshanba (Wednesday)",
    "pa": "Payshanba (Thursday)",
    "ju": "Juma (Friday)",
}

# Each day is a list of 7 slots (lessons 1-7). A slot is either a dict
# describing the lesson, or None if the slot is unused that day.
#
# NOTE on data quality: in the Friday (ju) lesson 6 entry, the source spec
# gave "Room: Xursand / Umarbek" with no separate teacher field and no
# actual room number. That looks like a copy/paste slip in the original
# schedule. I've encoded it as room=None with those two names kept as the
# teachers, so nothing is silently dropped — please confirm the real room
# number and fix TIMETABLE["ju"][5]["room"] below.
TIMETABLE = {
    "du": [
        {"subject": "Algebra", "room": "218", "teachers": ["Umid", "Muhammadsodiq"]},
        {"subject": "Kelajak soati", "room": "204", "teachers": ["Umarbek"]},
        {"subject": "Ona tili", "room": "208", "teachers": ["Q.Umid"]},
        {"subject": "Informatika", "room": "220", "teachers": ["Xursand", "Umarbek"]},
        {"subject": "Ingliz tili", "room": "128", "teachers": ["Rufat", "Muzaffar"]},
        {"subject": "Rus tili", "room": "202", "teachers": ["Gulzoda", "Sevara"]},
        {"subject": "Fizika", "room": "202", "teachers": ["O'g'lijon", "Ulug'bek"]},
    ],
    "se": [
        {"subject": "O'zbek tarix", "room": "113", "teachers": ["Murod"]},
        {"subject": "Adabiyot", "room": "208", "teachers": ["Q.Umid"]},
        {"subject": "Algebra", "room": "218", "teachers": ["Umid", "Muhammadsodiq"]},
        {"subject": "Geometriya", "room": "218", "teachers": ["Umid", "Muhammadsodiq"]},
        {"subject": "CHQBT", "room": "220", "teachers": ["To'lqin"]},
        {"subject": "Ingliz tili", "room": "220", "teachers": ["Rufat", "Muzaffar"]},
        {"subject": "Fizika", "room": "202", "teachers": ["O'g'lijon", "Ulug'bek"]},
    ],
    "ch": [
        {"subject": "Ona tili", "room": "208", "teachers": ["Q.Umid"]},
        {"subject": "Algebra", "room": "218", "teachers": ["Umid", "Muhammadsodiq"]},
        {"subject": "Fizika", "room": "218", "teachers": ["O'g'lijon", "Ulug'bek"]},
        {"subject": "Rus tili", "room": "128", "teachers": ["Gulzoda", "Sevara"]},
        {"subject": "Ingliz tili", "room": "220", "teachers": ["Rufat", "Muzaffar"]},
        {"subject": "CHQBT", "room": "129", "teachers": ["To'lqin"]},
        None,
    ],
    "pa": [
        {"subject": "Tarbiya", "room": "132", "teachers": ["Azada"]},
        {"subject": "Fizika", "room": "218", "teachers": ["O'g'lijon", "Ulug'bek"]},
        {"subject": "Algebra", "room": "218", "teachers": ["Umid", "Muhammadsodiq"]},
        {"subject": "Geometriya", "room": "218", "teachers": ["Umid", "Muhammadsodiq"]},
        {"subject": "Ingliz tili", "room": "220", "teachers": ["Rufat", "Muzaffar"]},
        {"subject": "Adabiyot", "room": "208", "teachers": ["Q.Umid"]},
        None,
    ],
    "ju": [
        {"subject": "Jismoniy tarbiya", "room": "Sport zal", "teachers": ["Ulug'bek"]},
        {"subject": "Geometriya", "room": "218", "teachers": ["Umid", "Muhammadsodiq"]},
        {"subject": "O'zbek tarix", "room": "113", "teachers": ["Murod"]},
        {"subject": "Fizika", "room": "202", "teachers": ["O'g'lijon", "Ulug'bek"]},
        {"subject": "Jahon tarix", "room": "113", "teachers": ["Murod"]},
        # See data-quality note above — room is unconfirmed for this slot.
        {"subject": "Informatika", "room": None, "teachers": ["Xursand", "Umarbek"]},
        None,
    ],
}
