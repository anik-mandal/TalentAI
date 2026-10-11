import sys
import os
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
from groq import Groq

# allow importing shared modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from shared.db import get_supabase, get_secret
from shared.chroma_setup import get_job_context, get_candidates_collection

load_dotenv()

# -----------------------------
# GROQ CONFIG
# -----------------------------

client = Groq(
    api_key=get_secret("GROQ_API_KEY")
)

# Supabase connection
supabase = get_supabase()


# -----------------------------
# SCREEN ONE CANDIDATE
# -----------------------------

def screen_one_candidate(resume_text, job_context):

    prompt = f"""
You are a senior HR screener. Score this candidate ONLY against the company
requirements below. Do not use generic opinions.

COMPANY REQUIREMENTS (from ChromaDB — RAG):
{job_context}

CANDIDATE RESUME:
{resume_text}

Return ONLY valid JSON — no markdown, no explanation:

{{
"screening_score": <0-100>,
"skills_matched": ["skill1", "skill2"],
"skills_missing": ["skill3", "skill4"],
"experience_fit": "<good|average|poor>",
"culture_fit": "<good|average|poor>",
"recommendation": "<shortlist|reject|maybe>",
"screening_reason": "<2-3 sentence explanation of why this score was given>",
"summary": "<two sentences>"
}}
"""

    try:

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        raw = response.choices[0].message.content.strip()

        # clean markdown formatting if present
        if "```" in raw:
            raw = raw.split("```")[1]

        if raw.startswith("json"):
            raw = raw[4:]

        raw = raw.strip()

        return json.loads(raw)

    except Exception as e:

        print("⚠ Groq returned invalid JSON. Using fallback result.")
        print(e)

        return {
            "screening_score": 50,
            "skills_matched": [],
            "skills_missing": [],
            "experience_fit": "average",
            "culture_fit": "average",
            "recommendation": "maybe",
            "screening_reason": "Fallback result due to parsing error.",
            "summary": "Fallback result due to parsing error."
        }


# -----------------------------
# RUN SCREENING
# -----------------------------

def run_screening(job_id):

    job_context = get_job_context(job_id)

    if not job_context:
        print(f"ChromaDB empty for Job {job_id}, fetching from Supabase...")
        try:
            job_row = supabase.table("jobs").select("*").eq("id", job_id).execute()
            if job_row.data:
                j = job_row.data[0]
                job_context = (
                    f"Company: {j.get('company_name','')}\n"
                    f"Job Title: {j.get('job_title','')}\n"
                    f"Skills Required: {j.get('skills_required','')}\n"
                    f"Requirements: {j.get('requirements','')}\n"
                    f"Experience: {j.get('experience_years','')}\n"
                )
                from shared.chroma_setup import store_job_in_chroma
                store_job_in_chroma(job_id, job_context)
        except Exception as e:
            print("Fallback job fetch error:", e)

    if not job_context:
        print(f"❌ Job {job_id} not found in ChromaDB or Supabase.")
        return "Failed"

    result = (
        supabase.table("candidates")
        .select("*")
        .eq("job_id", job_id)
        .in_("status", ["applied", "sourced_qualified"])
        .execute()
    )

    candidates = result.data

    if not candidates:
        print(f"No candidates found for job {job_id}.")
        return "No candidates"

    print(f"\nScreening {len(candidates)} candidates for job {job_id}")
    print("=" * 55)

    shortlisted = 0
    rejected = 0
    maybe = 0

    for c in candidates:

        print(f"Screening: {c['name']}...")

        try:

            score = screen_one_candidate(c["resume_text"], job_context)

            # Score-based status logic
            screening_score = score["screening_score"]

            if screening_score >= 70:
                new_status = "shortlisted"
            elif screening_score >= 50:
                new_status = "maybe"
            else:
                new_status = "rejected"

            # -----------------------------
            # Telegram notification
            # -----------------------------

            if new_status == "shortlisted":
                try:
                    from engagement.telegram_notifier import send_shortlist_notification

                    send_shortlist_notification(
                        candidate_name=c["name"],
                        chat_id=c.get("telegram_chat_id"),
                        job_title=c.get("job_applied", "")
                    )

                except Exception as e:
                    print("Telegram shortlist notification failed:", e)

            # -----------------------------
            # Update Supabase
            # -----------------------------

            supabase.table("candidates").update({

                "screening_score": screening_score,
                "skills_matched": ", ".join(score.get("skills_matched", [])),
                "skills_missing": ", ".join(score.get("skills_missing", [])),
                "culture_fit": score.get("culture_fit", ""),
                "recommendation": score.get("recommendation", ""),
                "screening_reason": score.get("screening_reason", score.get("summary", "")),
                "status": new_status

            }).eq("id", c["id"]).execute()

            # -----------------------------
            # Store in ChromaDB
            # -----------------------------

            coll = get_candidates_collection()

            coll.upsert(
                documents=[f"Score:{score['screening_score']} {c['resume_text'][:300]}"],
                ids=[str(c["id"])]
            )

            print(f"✓ {score['screening_score']}/100 → {new_status.upper()}")

            if new_status == "shortlisted":
                shortlisted += 1
            elif new_status == "rejected":
                rejected += 1
            else:
                maybe += 1

        except Exception as e:

            print(f"✗ Error screening {c['name']}: {e}")

            supabase.table("candidates").update(
                {"status": "maybe"}
            ).eq("id", c["id"]).execute()

    summary = f"Done. Shortlisted: {shortlisted} | Maybe: {maybe} | Rejected: {rejected}"

    print(f"\n{summary}")

    return summary


# -----------------------------
# MAIN
# -----------------------------

if __name__ == "__main__":

    job_id = int(input("Enter Job ID: "))

    run_screening(job_id)