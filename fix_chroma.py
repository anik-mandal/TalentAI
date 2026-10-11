import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.db import get_supabase
from shared.chroma_setup import store_job_in_chroma, get_job_context

supabase = get_supabase()

print("Fetching all jobs from Supabase...")

jobs = supabase.table("jobs").select("*").execute().data

if not jobs:
    print("No jobs found in Supabase!")
else:
    for job in jobs:
        job_text = (
            f"Company: {job['company_name']} | Job: {job['job_title']}\n"
            f"Description: {job['requirements']}\n"
            f"Skills: {job['skills_required']}\n"
            f"Experience: {job['experience_years']}\n"
            f"Culture: {job.get('culture_description', '')}\n"
            f"Dealbreakers: {job.get('dealbreakers', '')}"
        )
        store_job_in_chroma(job["id"], job_text)
        print(f"Pushed Job ID {job['id']} — {job['job_title']}")

    print("\nVerifying...")
    for job in jobs:
        context = get_job_context(job["id"])
        if context:
            print(f"✅ Job ID {job['id']} verified in ChromaDB")
        else:
            print(f"❌ Job ID {job['id']} FAILED")