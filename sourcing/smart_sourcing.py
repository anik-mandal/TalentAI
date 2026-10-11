"""
smart_sourcing.py  -  Member 1 | Days 4-5

- Uses new google-genai package (no deprecation warning)
- Gets job context from Supabase directly (no ChromaDB needed)
- Inserts candidates with all columns: resume_text, status, source_quality_score

Run from project ROOT:
    python sourcing/smart_sourcing.py
"""

import os
import json
import requests
from supabase import create_client
from dotenv import load_dotenv
from google import genai

# ── Load .env ─────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(dotenv_path=os.path.join(ROOT, ".env"))

# ── Gemini client (new SDK) ───────────────────────────────────
gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ── Supabase client ───────────────────────────────────────────
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


# ─────────────────────────────────────────────────────────────
def ask_gemini(prompt: str) -> str:
    """Send a prompt to Gemini and return the response text."""
    response = gemini.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return response.text.strip()


# ─────────────────────────────────────────────────────────────
def get_job_context(job_id: int) -> str:
    """
    Get job details from Supabase jobs table.
    No ChromaDB import needed.
    """
    result = supabase.table("jobs").select("*").eq("id", job_id).execute()
    if not result.data:
        return ""

    j = result.data[0]
    return (
        f"Job Title: {j.get('job_title', '')}\n"
        f"Company: {j.get('company_name', '')}\n"
        f"Requirements: {j.get('requirements', '')}\n"
        f"Skills Required: {j.get('skills_required', '')}\n"
        f"Experience Needed: {j.get('experience_years', '')}\n"
        f"Location: {j.get('location', '')}\n"
    )


# ─────────────────────────────────────────────────────────────
def fetch_profiles(count: int = 15) -> list:
    """Fetch simulated Indian candidate profiles from randomuser.me."""
    try:
        r = requests.get(
            f"https://randomuser.me/api/?results={count}&nat=in",
            timeout=10
        )
        r.raise_for_status()
        print(f"✅ Fetched {count} profiles from randomuser.me")
        return r.json()["results"]
    except Exception as e:
        print(f"❌ Could not fetch profiles: {e}")
        return []


# ─────────────────────────────────────────────────────────────
def build_profile_text(p: dict) -> str:
    """Convert a randomuser.me profile dict into readable text."""
    age = p['dob']['age']

    if age < 25:
        skills = "Python basics, SQL, Excel, college projects, 0-1 years exp"
    elif age < 30:
        skills = "Python, SQL, Pandas, REST APIs, Git, 2 years exp"
    elif age < 40:
        skills = "Python, SQL, Pandas, Power BI, team lead, 5 years exp"
    else:
        skills = "Python, SQL, data warehousing, management, 10+ years exp"

    return (
        f"Name: {p['name']['first']} {p['name']['last']}\n"
        f"Location: {p['location']['city']}, {p['location']['state']}\n"
        f"Age: {age}\n"
        f"Email: {p['email']}\n"
        f"Phone: {p['phone']}\n"
        f"Skills: {skills}\n"
    )


# ─────────────────────────────────────────────────────────────
def score_candidate(profile_text: str, job_context: str) -> dict:
    """Ask Gemini to score the candidate against job requirements."""
    prompt = f"""
You are a talent sourcing assistant.

JOB REQUIREMENTS:
{job_context}

CANDIDATE PROFILE:
{profile_text}

Return ONLY valid JSON. No markdown. No explanation. Nothing else:
{{
    "source_quality_score": <integer between 0 and 100>,
    "should_proceed": <true if score is 50 or above, false if below 50>,
    "reason": "<one short sentence explaining the score>"
}}
"""
    try:
        raw = ask_gemini(prompt)

        # Strip markdown fences if Gemini adds them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        return json.loads(raw.strip())

    except Exception as e:
        print(f"  ⚠️  Scoring error: {e} — defaulting to score 50")
        return {
            "source_quality_score": 50,
            "should_proceed": True,
            "reason": "Could not parse AI response"
        }


# ─────────────────────────────────────────────────────────────
def run_sourcing(job_id: int):
    """Full sourcing pipeline for a given job ID."""

    print(f"\n{'='*60}")
    print(f"  SMART SOURCING STARTING — JOB ID: {job_id}")
    print(f"{'='*60}\n")

    # Step 1 — Load job details from Supabase
    job_context = get_job_context(job_id)
    if not job_context:
        print(f"❌ Job ID {job_id} not found in Supabase.")
        print("   Ask Member 4 to post the job on the HR portal first.")
        return

    job_row   = supabase.table("jobs").select("job_title, company_name").eq("id", job_id).execute()
    job_title = job_row.data[0]["job_title"]
    company   = job_row.data[0]["company_name"]
    job_label = f"{job_title} at {company}"

    print(f"📋 Job : {job_label}")
    print(f"🔍 Fetching 15 candidate profiles...\n")

    # Step 2 — Fetch profiles
    profiles = fetch_profiles(15)
    if not profiles:
        return

    passed = 0
    filtered = 0

    print(f"  {'Name':<22} {'Score':>6}   Status")
    print(f"  {'-'*52}")

    # Step 3 — Score and insert each profile
    for p in profiles:
        profile_text = build_profile_text(p)
        result       = score_candidate(profile_text, job_context)
        name         = f"{p['name']['first']} {p['name']['last']}"
        status       = "sourced_qualified" if result["should_proceed"] else "sourced_filtered"

        supabase.table("candidates").insert({
            "name":                 name,
            "email":                p["email"],
            "phone":                p["phone"],
            "job_id":               job_id,
            "job_applied":          job_label,
            "resume_text":          profile_text,
            "status":               status,
            "source_quality_score": result["source_quality_score"],
        }).execute()

        icon  = "✅" if result["should_proceed"] else "❌"
        label = "QUALIFIED" if result["should_proceed"] else "FILTERED"
        print(f"  {icon} {name:<22} {result['source_quality_score']:>3}/100  {label}")

        if result["should_proceed"]:
            passed += 1
        else:
            filtered += 1

    # Step 4 — Print summary
    print(f"\n{'='*60}")
    print(f"  SOURCING COMPLETE")
    print(f"  ✅ Qualified : {passed}")
    print(f"  ❌ Filtered  : {filtered}")
    print(f"  📊 Total     : {passed + filtered}")
    print(f"{'='*60}")
    print(f"\n📌 Tell Member 4 to refresh dashboard → Candidate Pipeline tab.")


# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        job_id = int(input("Enter Job ID (use 4): ").strip())
        run_sourcing(job_id)
    except ValueError:
        print("❌ Please enter a valid number.")
    except KeyboardInterrupt:
        print("\nCancelled.")