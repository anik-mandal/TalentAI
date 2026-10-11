"""
seed_data.py — Populate realistic dev data for TalentAI Demonstration
Run: python seed_data.py
"""

import os
import sys
from datetime import datetime, date

# Force UTF-8 encoding for Windows console output
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from shared.db import get_supabase
from shared.chroma_setup import store_job_in_chroma, get_job_context

def seed():
    print("🌱 Connecting to Supabase...")
    supabase = get_supabase()

    # 1. SEED JOBS
    print("\n📝 Seeding Jobs...")
    jobs_data = [
        {
            "company_name": "Nexus AI Labs",
            "job_title": "Senior AI Engineer",
            "skills_required": "Python, PyTorch, LangChain, RAG, FastAPI, ChromaDB, Docker",
            "requirements": "3+ years building and deploying LLM pipelines, RAG systems, and fine-tuning models. Experience with vector databases and microservices.",
            "experience_years": "3-5 years",
            "location": "Bengaluru (Hybrid)",
            "salary_range": "₹18 - ₹26 LPA",
            "created_at": datetime.now().isoformat()
        },
        {
            "company_name": "CloudScale Systems",
            "job_title": "Full Stack Developer",
            "skills_required": "React, TypeScript, Node.js, PostgreSQL, Docker, TailwindCSS",
            "requirements": "Strong full-stack capabilities building responsive SaaS portals, REST APIs, and PostgreSQL database management.",
            "experience_years": "1-3 years",
            "location": "Remote",
            "salary_range": "₹10 - ₹15 LPA",
            "created_at": datetime.now().isoformat()
        }
    ]

    created_jobs = []
    for jd in jobs_data:
        check = supabase.table("jobs").select("*").eq("company_name", jd["company_name"]).eq("job_title", jd["job_title"]).execute()
        if check.data:
            job_record = check.data[0]
            print(f"  ⚡ Job already exists: {jd['job_title']} at {jd['company_name']} (ID: {job_record['id']})")
        else:
            res = supabase.table("jobs").insert(jd).execute()
            job_record = res.data[0]
            print(f"  ✅ Created Job: {jd['job_title']} at {jd['company_name']} (ID: {job_record['id']})")
        
        created_jobs.append(job_record)

        # Store in ChromaDB for RAG
        job_text = f"""Company: {job_record['company_name']}
Job Title: {job_record['job_title']}
Skills Required: {job_record['skills_required']}
Requirements: {job_record['requirements']}
Experience: {job_record.get('experience_years','')}
Location: {job_record.get('location','')}
"""
        store_job_in_chroma(job_record["id"], job_text)
        print(f"  🧠 Stored Job ID {job_record['id']} in ChromaDB (Context length: {len(job_text)} chars)")

    ai_job_id = created_jobs[0]["id"]
    ai_job_label = f"{created_jobs[0]['job_title']} at {created_jobs[0]['company_name']} (ID: {ai_job_id})"

    # 2. SEED CANDIDATES
    print("\n👥 Seeding Candidates...")
    candidates = [
        # Candidates in 'applied' status (READY FOR LIVE SCREENING IN DEMO)
        {
            "name": "Rohan Deshmukh",
            "email": "rohan.deshmukh@example.com",
            "phone": "+91 98765 43210",
            "job_id": ai_job_id,
            "job_applied": ai_job_label,
            "resume_text": "Experienced Python & Machine Learning Engineer with 4 years at fintech startups. Deep expertise in LangChain, RAG architecture, PyTorch, and vector databases (ChromaDB, Pinecone). Developed real-time retrieval systems using FastAPI and Docker.",
            "status": "applied",
            "source_quality_score": 88
        },
        {
            "name": "Ananya Sen",
            "email": "ananya.sen@example.com",
            "phone": "+91 98765 43211",
            "job_id": ai_job_id,
            "job_applied": ai_job_label,
            "resume_text": "Recent Data Science graduate. Solid foundation in Python, pandas, and scikit-learn. Completed academic projects using Flask and basic NLP sentiment analysis. Looking to learn LLM fine-tuning and production RAG pipelines.",
            "status": "applied",
            "source_quality_score": 58
        },
        {
            "name": "Vikas Verma",
            "email": "vikas.verma@example.com",
            "phone": "+91 98765 43212",
            "job_id": ai_job_id,
            "job_applied": ai_job_label,
            "resume_text": "Senior Java Backend Developer with 6 years experience in Spring Boot, Hibernate, microservices, and Oracle DB. Strong database optimization skills. No direct experience in Python or AI/LLMs.",
            "status": "applied",
            "source_quality_score": 30
        },
        # Already Screened Candidates (so HR Dashboard and Analytics have immediate data)
        {
            "name": "Priyanka Nair",
            "email": "priyanka.nair@example.com",
            "phone": "+91 98765 43213",
            "job_id": ai_job_id,
            "job_applied": ai_job_label,
            "resume_text": "Senior AI Researcher & Engineer. 5 years building production LLMs, PyTorch, vector search, RAG, and FastAPI microservices.",
            "status": "shortlisted",
            "source_quality_score": 92,
            "screening_score": 95,
            "skills_matched": "Python, PyTorch, LangChain, RAG, FastAPI, ChromaDB",
            "skills_missing": "None significant",
            "culture_fit": "good",
            "recommendation": "shortlist",
            "screening_reason": "Top-tier AI engineer with proven production RAG and LLM deployment expertise."
        },
        {
            "name": "Kunal Sharma",
            "email": "kunal.sharma@example.com",
            "phone": "+91 98765 43214",
            "job_id": ai_job_id,
            "job_applied": ai_job_label,
            "resume_text": "PHP & WordPress developer with 4 years building e-commerce plugins. Eager to transition into AI development.",
            "status": "rejected",
            "source_quality_score": 25,
            "screening_score": 22,
            "skills_matched": "General web development",
            "skills_missing": "Python, PyTorch, LangChain, RAG, Vector DBs",
            "culture_fit": "average",
            "recommendation": "reject",
            "screening_reason": "Background is entirely in PHP/CMS; lacks required Python, ML, and generative AI skills."
        }
    ]

    for c in candidates:
        chk = supabase.table("candidates").select("id").eq("email", c["email"]).execute()
        if not chk.data:
            supabase.table("candidates").insert(c).execute()
            print(f"  ✅ Added candidate: {c['name']} (Status: {c['status']})")
        else:
            print(f"  ⚡ Candidate exists: {c['name']}")

    # 3. SEED INTERVIEW SLOTS
    print("\n📅 Seeding Interview Slots...")
    slots = [
        {"date": "2026-10-15", "time": "10:00 AM", "interviewer_name": "Dr. Sarah Jenkins", "is_booked": False},
        {"date": "2026-10-15", "time": "02:00 PM", "interviewer_name": "Dr. Sarah Jenkins", "is_booked": False},
        {"date": "2026-10-16", "time": "11:00 AM", "interviewer_name": "Alex Mercer (Tech Lead)", "is_booked": False},
        {"date": "2026-10-16", "time": "04:00 PM", "interviewer_name": "Alex Mercer (Tech Lead)", "is_booked": True, "candidate_name": "Priyanka Nair"}
    ]

    for s in slots:
        chk = supabase.table("interview_slots").select("id").eq("date", s["date"]).eq("time", s["time"]).eq("interviewer_name", s["interviewer_name"]).execute()
        if not chk.data:
            supabase.table("interview_slots").insert(s).execute()
            print(f"  ✅ Added slot: {s['date']} at {s['time']} ({s['interviewer_name']})")
        else:
            print(f"  ⚡ Slot exists: {s['date']} at {s['time']}")

    # 4. SEED SAMPLE CHAT LOG
    print("\n💬 Seeding Chat Logs...")
    logs = [
        {"email": "priyanka.nair@example.com", "question": "What is the tech stack for the Senior AI Engineer role?", "answer": "The tech stack comprises Python, PyTorch, LangChain, RAG architectures, FastAPI microservices, and ChromaDB for vector retrieval."}
    ]
    for log in logs:
        chk = supabase.table("chat_logs").select("id").eq("email", log["email"]).eq("question", log["question"]).execute()
        if not chk.data:
            supabase.table("chat_logs").insert(log).execute()
            print(f"  ✅ Added sample chat log for {log['email']}")

    print("\n" + "="*60)
    print("✨ DUMMY DATA SEEDING COMPLETE!")
    print("="*60)
    print("Verification:")
    print(f"• ChromaDB context test for Job {ai_job_id}:")
    ctx = get_job_context(ai_job_id)
    print(f"  Retrieved: {ctx[:100]}...")

if __name__ == "__main__":
    seed()
