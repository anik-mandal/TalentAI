"""
candidate_service.py
Resume parsing + Groq AI scoring + DB insertion
"""

import os
import sys
import io
import PyPDF2
from dotenv import load_dotenv
from groq import Groq

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from sourcing.candidate_ingestion import add_candidate

load_dotenv()

# Initialize Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ------------------------------------------------
# Extract text from PDF
# ------------------------------------------------

def extract_pdf(file_bytes: bytes) -> str:

    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = "".join(page.extract_text() or "" for page in reader.pages)
        return text.strip() or "Could not extract text."

    except Exception as e:
        return f"PDF error: {e}"


# ------------------------------------------------
# Groq AI Resume Scoring
# ------------------------------------------------

def score_resume(resume_text: str, job_title: str) -> int:

    prompt = f"""
You are an AI recruiter.

Evaluate how well this candidate matches the job.

JOB ROLE:
{job_title}

RESUME:
{resume_text}

Return ONLY a number between 0 and 100.
Example:
78
"""

    try:

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        score = response.choices[0].message.content.strip()

        score = int(score)

        return score

    except Exception as e:

        print("⚠️ Groq scoring error:", e)

        return 50


# ------------------------------------------------
# Candidate Ingestion
# ------------------------------------------------

def ingest_from_upload(
        name,
        email,
        phone,
        job_applied,
        pdf_bytes,
        job_id=None,
        experience="",
        cover_note="",
        telegram_chat_id=None
):

    resume_text = extract_pdf(pdf_bytes)

    full_resume = f"""
Experience: {experience}
Cover Note: {cover_note}

------ RESUME ------
{resume_text}
"""

    print("Scoring resume with Groq...")

    score = score_resume(full_resume, job_applied)

    print(f"AI Score: {score}")

    return add_candidate(
        name=name,
        email=email,
        phone=phone,
        job_applied=job_applied,
        job_id=job_id,
        resume_text=full_resume,
        status="applied",
        source_quality_score=score,
        telegram_chat_id=telegram_chat_id
    )


# ------------------------------------------------
# Quick Test
# ------------------------------------------------

if __name__ == "__main__":

    sample_resume = b"Sample resume text"

    ingest_from_upload(
        name="Rahul Sharma",
        email="rahul@test.com",
        phone="9999999999",
        job_applied="AI Engineer",
        pdf_bytes=sample_resume,
        job_id=4,
        experience="2 years Python, FastAPI",
        cover_note="Interested in ML roles."
    )