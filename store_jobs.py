from shared.db import get_supabase
from shared.chroma_setup import store_job_in_chroma

supabase = get_supabase()

jobs = supabase.table("jobs").select("*").execute().data

if not jobs:
    print("No jobs found in Supabase.")
else:
    for j in jobs:

        job_text = f"""
Job Title: {j.get('job_title','')}
Company: {j.get('company_name','')}
Requirements: {j.get('requirements','')}
Skills Required: {j.get('skills_required','')}
Experience Needed: {j.get('experience_years','')}
"""

        store_job_in_chroma(j["id"], job_text)

        print(f"Stored Job {j['id']} in ChromaDB")