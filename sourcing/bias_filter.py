"""
bias_filter.py  -  Member 1 | Day 6
Uses new google-genai SDK (gemini-2.0-flash) — no deprecation errors.

Run from project ROOT:
    python sourcing/bias_filter.py
"""

import os
import json
from collections import Counter
from supabase import create_client
from dotenv import load_dotenv
from google import genai

# ── Load .env ─────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(dotenv_path=os.path.join(ROOT, ".env"))

# ── Clients ───────────────────────────────────────────────────
gemini   = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


def ask_gemini(prompt: str) -> str:
    """Call Gemini 2.0 Flash and return response text."""
    response = gemini.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return response.text.strip()


def anonymize_profile(resume_text: str) -> dict:
    """Ask Gemini to remove bias signals from resume text."""
    prompt = f"""
Anonymize this candidate profile for fair hiring.

Remove these completely:
- Real name (replace with "Candidate")
- Gender pronouns: he, she, his, her, him (replace with they/their)
- Exact age or date of birth
- City or town names
- College or university names

Keep these exactly as they are:
- Technical skills (Python, SQL, etc.)
- Years of experience
- Job titles
- Achievements and numbers
- Degree type only (B.Tech, MBA, etc.)

Profile to anonymize:
{resume_text}

Return ONLY valid JSON. No markdown. Nothing else:
{{
    "anonymized_text": "<cleaned profile text here>",
    "signals_removed": ["<item1>", "<item2>"]
}}
"""
    try:
        raw = ask_gemini(prompt)

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        return json.loads(raw.strip())

    except Exception as e:
        print(f"  ⚠️  Anonymization error: {e} — keeping original text")
        return {"anonymized_text": resume_text, "signals_removed": []}


def apply_bias_filter(job_id: int):
    """Anonymize all candidates for a given job_id."""

    print(f"\n{'='*55}")
    print(f"  BIAS FILTER — JOB ID: {job_id}")
    print(f"{'='*55}\n")

    # Fetch ALL candidates for this job (not just sourced_qualified)
    # because names were already anonymized in the previous run
    result = supabase.table("candidates") \
        .select("id, name, resume_text") \
        .eq("job_id", job_id) \
        .execute()

    candidates = result.data

    if not candidates:
        print(f"No candidates found for Job ID {job_id}.")
        return

    print(f"Found {len(candidates)} candidates to anonymize...\n")

    all_signals = []
    success     = 0

    for c in candidates:
        cid          = c["id"]
        resume_text  = c.get("resume_text", "") or ""

        print(f"  Processing Candidate_{cid}...")

        anon    = anonymize_profile(resume_text)
        signals = anon.get("signals_removed", [])
        all_signals.extend(signals)

        # Update resume_text in Supabase with anonymized version
        # Name is already Candidate_X from previous run — keep it
        supabase.table("candidates").update({
            "name":        f"Candidate_{cid}",
            "resume_text": anon["anonymized_text"],
        }).eq("id", cid).execute()

        print(f"  ✅ Done — signals removed: {signals if signals else 'none detected'}")
        success += 1

    # Summary
    top = dict(Counter(all_signals).most_common(6))

    print(f"\n{'='*55}")
    print(f"  BIAS FILTER COMPLETE")
    print(f"  ✅ Candidates processed : {success}")
    if top:
        print(f"  Top bias signals removed:")
        for k, v in top.items():
            print(f"    • {k}: {v}x")
    else:
        print(f"  (No bias signals detected in profiles)")
    print(f"{'='*55}")
    print(f"\nScreening module will now judge on skills only.")


if __name__ == "__main__":
    try:
        job_id = int(input("Enter Job ID (use 4): ").strip())
        apply_bias_filter(job_id)
    except ValueError:
        print("❌ Enter a valid number.")
    except KeyboardInterrupt:
        print("\nCancelled.")