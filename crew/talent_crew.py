"""
talent_crew.py  -  Member 1 | Days 7-11
────────────────────────────────────────
3-agent pipeline that WRITES results back to Supabase.
After running, Member 4's dashboard will show pipeline data.

Writes to candidates table:
  - status        → shortlisted / maybe / rejected
  - recommendation → AI-generated one-line recommendation
  - screening_score → 0-100 score from Agent 2

Run from project ROOT:
    python crew/talent_crew.py
"""

import os
import json
import time
from supabase import create_client
from dotenv import load_dotenv
from google import genai

# ── Load .env ─────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(dotenv_path=os.path.join(ROOT, ".env"))

gemini   = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


# ─────────────────────────────────────────────────────────────
def ask_gemini(prompt: str) -> str:
    try:
        response = gemini.models.generate_content(
            model    = "gemini-2.0-flash",
            contents = prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"  ⚠️  Gemini error: {e}")
        return ""


# ─────────────────────────────────────────────────────────────
def get_job_details(job_id: int) -> str:
    result = supabase.table("jobs").select("*").eq("id", job_id).execute()
    if not result.data:
        return ""
    j = result.data[0]
    return (
        f"Job Title: {j.get('job_title','')}\n"
        f"Company: {j.get('company_name','')}\n"
        f"Skills Required: {j.get('skills_required','')}\n"
        f"Experience: {j.get('experience_years','')}\n"
    )


def get_all_candidates(job_id: int) -> list:
    result = supabase.table("candidates") \
        .select("id, name, email, resume_text, status, source_quality_score") \
        .eq("job_id", job_id) \
        .execute()
    return result.data or []


# ─────────────────────────────────────────────────────────────
def agent_1_sourcing(job_context: str, candidates: list) -> str:
    """Agent 1 — reviews and summarises sourced candidates."""

    print("\n" + "─"*60)
    print("  🤖 AGENT 1: Talent Sourcing Specialist — Running...")
    print("─"*60)

    cand_text = "\n".join([
        f"ID:{c['id']} | {c['name']} | "
        f"Score:{c.get('source_quality_score',0)} | "
        f"Status:{c.get('status','unknown')} | "
        f"Profile:{str(c.get('resume_text',''))[:100]}"
        for c in candidates
    ])

    prompt = f"""
You are a Talent Sourcing Specialist.

JOB: {job_context}

SOURCED CANDIDATES:
{cand_text}

Count sourced_qualified vs sourced_filtered vs applied.
Name the top 5 most promising candidates based on skills.
Write a brief sourcing summary.
"""
    result = ask_gemini(prompt)
    print(result)
    return result


# ─────────────────────────────────────────────────────────────
def agent_2_screening(job_context: str, candidates: list) -> list:
    """
    Agent 2 — scores each candidate individually and saves to Supabase.
    Returns list of scored candidates.
    """

    print("\n" + "─"*60)
    print("  🤖 AGENT 2: Resume Screening Expert — Running...")
    print("─"*60)

    scored = []

    for i, c in enumerate(candidates):
        # Wait every 3 candidates to avoid rate limit
        if i > 0 and i % 3 == 0:
            print(f"  ⏳ Pausing 20s to avoid rate limit...")
            time.sleep(20)

        prompt = f"""
You are a Resume Screening Expert.

JOB REQUIREMENTS:
{job_context}

CANDIDATE PROFILE:
Name: {c['name']}
Profile: {str(c.get('resume_text',''))[:300]}
Current Score: {c.get('source_quality_score', 0)}

Return ONLY valid JSON, no markdown:
{{
    "screening_score": <integer 0-100>,
    "status": "<shortlisted if score>=70, maybe if 40-69, rejected if below 40>",
    "recommendation": "<one sentence recommendation for HR manager>"
}}
"""
        raw = ask_gemini(prompt)

        try:
            # Clean markdown fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            result = json.loads(raw.strip())
        except Exception:
            result = {
                "screening_score": 50,
                "status": "maybe",
                "recommendation": "Moderate match — requires further review."
            }

        # Save results to Supabase immediately
        update_data = {
            "status":         result["status"],
            "recommendation": result["recommendation"],
        }

        # Only update screening_score if column exists
        try:
            supabase.table("candidates").update({
                **update_data,
                "screening_score": result["screening_score"]
            }).eq("id", c["id"]).execute()
        except Exception:
            # If screening_score column doesn't exist, save without it
            supabase.table("candidates").update(
                update_data
            ).eq("id", c["id"]).execute()

        icon = "✅" if result["status"] == "shortlisted" else (
               "🤔" if result["status"] == "maybe" else "❌")

        print(
            f"  {icon} {c['name']:<20} "
            f"{result['screening_score']:>3}/100  "
            f"{result['status']:<12}  "
            f"{result['recommendation'][:40]}"
        )

        scored.append({**c, **result})

    return scored


# ─────────────────────────────────────────────────────────────
def agent_3_engagement(job_context: str, scored_candidates: list) -> str:
    """Agent 3 — writes final HR engagement report."""

    print("\n" + "─"*60)
    print("  🤖 AGENT 3: Candidate Engagement Coordinator — Running...")
    print("─"*60)

    shortlisted = [c for c in scored_candidates if c.get("status") == "shortlisted"]
    maybe       = [c for c in scored_candidates if c.get("status") == "maybe"]
    rejected    = [c for c in scored_candidates if c.get("status") == "rejected"]

    shortlisted_text = "\n".join([
        f"- {c['name']} | {c['email']} | "
        f"Score:{c.get('screening_score',0)} | "
        f"{c.get('recommendation','')}"
        for c in shortlisted
    ]) or "None"

    prompt = f"""
You are a Candidate Engagement Coordinator writing a report for the HR Manager.

JOB: {job_context}

SCREENING RESULTS:
Total reviewed: {len(scored_candidates)}
Shortlisted ({len(shortlisted)}):
{shortlisted_text}
Maybe: {len(maybe)} candidates
Rejected: {len(rejected)} candidates

Write a professional, brief HR engagement report with:
1. Summary of pipeline results
2. Top shortlisted candidates to contact first
3. Recommended immediate next steps
"""
    result = ask_gemini(prompt)
    print(result)
    return result


# ─────────────────────────────────────────────────────────────
def run_pipeline(job_id: int):

    print(f"\n{'='*60}")
    print(f"  TALENT ACQUISITION PIPELINE — JOB ID: {job_id}")
    print(f"  3 AI Agents | Results saved to Supabase")
    print(f"{'='*60}\n")

    job_context = get_job_details(job_id)
    if not job_context:
        print(f"❌ Job ID {job_id} not found.")
        return

    candidates = get_all_candidates(job_id)
    if not candidates:
        print(f"❌ No candidates found for Job ID {job_id}.")
        return

    print(f"✅ Job: {job_context.splitlines()[0]}")
    print(f"✅ {len(candidates)} candidates to process\n")

    # Agent 1 — Sourcing review
    agent_1_sourcing(job_context, candidates)

    print("\n⏳ Waiting 20s before Agent 2...")
    time.sleep(20)

    # Agent 2 — Screen every candidate + save to Supabase
    scored = agent_2_screening(job_context, candidates)

    print("\n⏳ Waiting 20s before Agent 3...")
    time.sleep(20)

    # Agent 3 — Final engagement report
    agent_3_engagement(job_context, scored)

    # Summary
    shortlisted = sum(1 for c in scored if c.get("status") == "shortlisted")
    maybe       = sum(1 for c in scored if c.get("status") == "maybe")
    rejected    = sum(1 for c in scored if c.get("status") == "rejected")

    print(f"\n{'='*60}")
    print(f"  ✅ PIPELINE COMPLETE — ALL 3 AGENTS FINISHED")
    print(f"  📊 Results saved to Supabase:")
    print(f"     ✅ Shortlisted : {shortlisted}")
    print(f"     🤔 Maybe       : {maybe}")
    print(f"     ❌ Rejected    : {rejected}")
    print(f"{'='*60}")
    print(f"\n📌 Tell Member 4 to refresh dashboard — pipeline should now show data.")


# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        job_id = int(input("Enter Job ID (use 4): ").strip())
        run_pipeline(job_id)
    except ValueError:
        print("❌ Enter a valid number.")
    except KeyboardInterrupt:
        print("\nCancelled.")
    except Exception as e:
        print(f"\n❌ Error: {e}")