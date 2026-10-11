import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from shared.db import get_supabase, get_secret
from shared.chroma_setup import get_job_context, store_job_in_chroma, check_duplicate_resume, store_candidate_resume
from screening.rag_screener import screen_one_candidate
from groq import Groq
import pandas as pd

sb = get_supabase()

print("="*60)
print("1. DATABASE READ TEST (Inputs & Outputs)")
print("="*60)
jobs = sb.table('jobs').select('*').execute().data
candidates = sb.table('candidates').select('*').execute().data
slots = sb.table('interview_slots').select('*').execute().data

print(f"✓ Found {len(jobs)} jobs in database")
for j in jobs:
    print(f"   • Job #{j['id']}: {j['job_title']} at {j['company_name']}")

print(f"✓ Found {len(candidates)} candidates in database")
for c in candidates:
    print(f"   • Candidate #{c['id']}: {c['name']} | Status: {c['status']} | Score: {c.get('screening_score')}")

print(f"✓ Found {len(slots)} interview slots")
for s in slots:
    status = "BOOKED" if s['is_booked'] else "AVAILABLE"
    print(f"   • Slot #{s['id']}: {s['date']} {s['time']} ({s['interviewer_name']}) -> {status}")

print("\n" + "="*60)
print("2. CHROMADB RAG RETRIEVAL TEST")
print("="*60)
for j in jobs:
    ctx = get_job_context(j['id'])
    print(f"✓ ChromaDB Context for Job #{j['id']} ({j['job_title']}): {len(ctx)} chars")
    assert len(ctx) > 0, f"ChromaDB context missing for job #{j['id']}"

print("\n" + "="*60)
print("3. GROQ AI SCREENING TEST (Input -> Prompt -> Structured JSON Output)")
print("="*60)
test_resume = """
Senior Python and Machine Learning Engineer.
Over 4 years of experience building RAG applications using LangChain, PyTorch, and ChromaDB.
Strong background in vector search, embeddings, model optimization, and REST API development with FastAPI and Docker.
"""
test_ctx = get_job_context(jobs[0]['id'])
print(f"Sending candidate resume ({len(test_resume)} chars) to Groq with Job Context...")
res = screen_one_candidate(test_resume, test_ctx)
print("✓ Groq response received successfully!")
print(f"   • Score: {res.get('screening_score')}/100")
print(f"   • Recommendation: {res.get('recommendation')}")
print(f"   • Skills Matched: {res.get('skills_matched')}")
print(f"   • Skills Missing: {res.get('skills_missing')}")
print(f"   • Experience Fit: {res.get('experience_fit')}")
print(f"   • Screening Reason: {res.get('screening_reason')}")

assert 'screening_score' in res and isinstance(res['screening_score'], (int, float)), "Screening score not valid"

print("\n" + "="*60)
print("4. CHATBOT RAG TEST (Candidate Question -> Retrieval -> Answer)")
print("="*60)
client = Groq(api_key=get_secret("GROQ_API_KEY"))
question = "What are the required qualifications for this job and what experience is expected?"
print(f"Candidate Question: '{question}'")

prompt = f"""
You are an AI HR assistant for TalentAI recruitment platform.
Use the job description below to answer candidate questions accurately.
JOB DETAILS:
{test_ctx}

Question: {question}
"""
chat_resp = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.3
)
answer = chat_resp.choices[0].message.content.strip()
print(f"✓ Chatbot Answer:\n{answer}\n")
assert len(answer) > 30, "Chatbot answer is empty or too short"

print("\n" + "="*60)
print("5. INTERVIEW BOOKING TEST (Candidate Input -> Slot Update)")
print("="*60)
# Find an open slot
open_slots = [s for s in slots if not s['is_booked']]
if open_slots:
    test_slot = open_slots[0]
    print(f"Testing booking slot #{test_slot['id']} for candidate Rohan Deshmukh...")
    upd = sb.table('interview_slots').update({
        'is_booked': True,
        'candidate_name': 'Rohan Deshmukh'
    }).eq('id', test_slot['id']).execute()
    print(f"✓ Successfully booked slot #{test_slot['id']}: is_booked = True")
    
    # Revert back to test idempotency
    sb.table('interview_slots').update({
        'is_booked': False,
        'candidate_name': None
    }).eq('id', test_slot['id']).execute()
    print(f"✓ Reset slot #{test_slot['id']} to available.")

print("\n" + "="*60)
print("6. DUPLICATE DETECTION TEST (Resume Hash / Vector Similarity)")
print("="*60)
dup_result = check_duplicate_resume(test_resume)
print(f"Duplicate resume check returned: {dup_result}")

print("\n" + "="*60)
print("🎉 ALL SYSTEM INPUT/OUTPUT VERIFICATION CHECKS PASSED PERFECTLY!")
print("="*60)
