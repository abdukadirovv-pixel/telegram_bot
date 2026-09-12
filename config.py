"""
Configuration and static data for the 10-B Aniq Lesson Reminder & Document
Vault bot.
"""

import os

# ---------------------------------------------------------------------------
# Bot credentials / environment
# ---------------------------------------------------------------------------

BOT_TOKEN = os.environ.get("BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")

# IANA timezone name used for schedules
TIMEZONE = "Asia/Tashkent"

# Where subscriber chat_ids and dynamic vault codes are persisted between restarts
SUBSCRIBERS_FILE = os.path.join(os.path.dirname(__file__), "subscribers.json")
VAULT_FILE = os.path.join(os.path.dirname(__file__), "vault.json")

# ---------------------------------------------------------------------------
# Secure Document Vault (Private Channel Integration)
# ---------------------------------------------------------------------------
# Your private storage channel numeric ID (Bot must be an admin here)
STORAGE_CHANNEL = -1004390673988

# Default fallback codes (Code -> Message ID in storage channel)
DEFAULT_SECRET_CODES = {
    # Add initial codes here if needed, or upload directly to your bot
}

# ---------------------------------------------------------------------------
# Daily Bell Schedule
# ---------------------------------------------------------------------------
BELL_SCHEDULE = [
    {"lesson": 1, "start": "09:00", "end": "09:45", "break_after": "5 min break"},
    {"lesson": 2, "start": "09:50", "end": "10:35", "break_after": "5 min break"},
    {"lesson": 3, "start": "10:40", "end": "11:25", "break_after": "5 min break"},
    {"lesson": 4, "start": "11:30", "end": "12:15", "break_after": "30 min lunch break"},
    {"lesson": 5, "start": "12:45", "end": "13:30", "break_after": "5 min break"},
    {"lesson": 6, "start": "13:35", "end": "14:20", "break_after": "5 min break"},
    {"lesson": 7, "start": "14:25", "end": "15:10", "break_after": "End of school day"},
]

REMINDER_HOUR = 8
REMINDER_MINUTE = 45

# ---------------------------------------------------------------------------
# Weekly Timetable Data (10-B Aniq)
# ---------------------------------------------------------------------------
DAY_CODES = ["du", "se", "ch", "pa", "ju"]

DAY_NAMES = {
    "du": "Dushanba (Monday)",
    "se": "Seshanba (Tuesday)",
    "ch": "Chorshanba (Wednesday)",
    "pa": "Payshanba (Thursday)",
    "ju": "Juma (Friday)",
}

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
        {"subject": "Informatika", "room": None, "teachers": ["Xursand", "Umarbek"]},
        None,
    ],
}