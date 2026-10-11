"""
candidate_ingestion.py
Handles inserting candidates into Supabase with AI scoring
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def add_candidate(
        name: str,
        email: str,
        phone: str,
        job_applied: str,
        job_id: int = None,
        resume_text: str = "",
        status: str = "applied",
        source_quality_score: int = 0,
        telegram_chat_id: str = None
) -> dict:
    """
    Insert candidate into Supabase candidates table
    """

    record = {
        "name": name,
        "email": email,
        "phone": phone,
        "job_applied": job_applied,
        "resume_text": resume_text[:5000],
        "status": status,
        "source_quality_score": source_quality_score,
    }

    if job_id is not None:
        record["job_id"] = job_id

    if telegram_chat_id:
        record["telegram_chat_id"] = telegram_chat_id

    result = supabase.table("candidates").insert(record).execute()

    print(
        f"✅ Inserted: {name} | score={source_quality_score} | status={status}"
    )

    return result.data[0] if result.data else {}


# test
if __name__ == "__main__":

    add_candidate(
        name="Test Candidate",
        email="test@example.com",
        phone="9999999999",
        job_applied="AI Engineer",
        job_id=4,
        resume_text="Python developer, FastAPI, SQL.",
        source_quality_score=70
    )