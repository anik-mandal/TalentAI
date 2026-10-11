import requests
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.db import get_secret

load_dotenv()

TELEGRAM_BOT_TOKEN = get_secret("TELEGRAM_BOT_TOKEN")


def send_interview_confirmation(
    candidate_name,
    chat_id,
    interviewer_name,
    date,
    time,
    job_title
):

    if not TELEGRAM_BOT_TOKEN or not chat_id:
        return

    message = f"""
🎉 Interview Confirmed!

Candidate: {candidate_name}
Role: {job_title}

📅 Date: {date}
⏰ Time: {time}
👤 Interviewer: {interviewer_name}

Please join 5 minutes early.

Good luck!
"""

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message
    }

    try:
        requests.post(url, json=payload)
    except:
        pass


def send_shortlist_notification(candidate_name, chat_id, job_title):
    """Send a Telegram notification when a candidate is shortlisted."""

    if not TELEGRAM_BOT_TOKEN or not chat_id:
        return

    message = f"""
🎉 Congratulations {candidate_name}!

You have been SHORTLISTED for the role:
{job_title}

Our HR team will contact you soon to schedule an interview.

Stay tuned!
— TalentAI
"""

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message
    }

    try:
        requests.post(url, json=payload)
    except:
        pass