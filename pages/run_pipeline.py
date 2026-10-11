"""
pages/run_pipeline.py — Run Screening Pipeline
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.db import get_supabase
from shared.ui_theme import apply_theme

apply_theme()

supabase = get_supabase()

# -------------------------------------------------
# HEADER
# -------------------------------------------------

st.markdown("<h1>⚙️ Run Screening Pipeline</h1>", unsafe_allow_html=True)
st.caption("Select a job and run the AI-powered RAG screening on pending candidates")
st.divider()

# -------------------------------------------------
# SELECT JOB
# -------------------------------------------------

jobs = supabase.table("jobs").select("id, job_title, company_name").execute().data

if not jobs:
    st.warning("No jobs posted yet. Please post a job first.")
    st.stop()

job_map = {
    f"{j['job_title']} at {j['company_name']} (ID: {j['id']})": j["id"]
    for j in jobs
}

selected_job = st.selectbox("Select Job to Screen", list(job_map.keys()))
job_id = job_map[selected_job]

# -------------------------------------------------
# PENDING CANDIDATES COUNT
# -------------------------------------------------

pending = (
    supabase.table("candidates")
    .select("id, name")
    .eq("job_id", job_id)
    .in_("status", ["applied", "sourced_qualified"])
    .execute()
)

pending_count = len(pending.data) if pending.data else 0

st.markdown("")

col1, col2 = st.columns(2)

col1.metric("📩 Pending Candidates", pending_count)

# Already screened
screened = (
    supabase.table("candidates")
    .select("id")
    .eq("job_id", job_id)
    .not_.in_("status", ["applied", "sourced_qualified"])
    .execute()
)

screened_count = len(screened.data) if screened.data else 0
col2.metric("✅ Already Screened", screened_count)

st.divider()

# -------------------------------------------------
# PENDING LIST
# -------------------------------------------------

if pending_count > 0:

    st.subheader(f"Candidates Awaiting Screening ({pending_count})")

    for c in pending.data:
        st.markdown(f"• {c['name']}")

    st.markdown("")

    # -------------------------------------------------
    # RUN PIPELINE BUTTON
    # -------------------------------------------------

    if st.button("🚀 Run Screening Pipeline", use_container_width=True):

        with st.spinner(f"Running AI screening on {pending_count} candidates..."):

            try:
                from screening.rag_screener import run_screening

                result = run_screening(job_id)

                st.success(f"✅ Screening completed for {pending_count} candidates!")
                st.info(f"📊 Result: {result}")

                st.balloons()

            except Exception as e:
                st.error(f"❌ Pipeline error: {e}")

else:

    st.info(
        "No pending candidates for this job. "
        "All candidates have already been screened, or no one has applied yet."
    )

# -------------------------------------------------
# RECENT RESULTS QUICK VIEW
# -------------------------------------------------

st.divider()
st.subheader("📋 Recent Screening Activity")

recent = (
    supabase.table("candidates")
    .select("name, screening_score, status, recommendation, screening_reason")
    .eq("job_id", job_id)
    .neq("status", "applied")
    .order("screening_score", desc=True)
    .limit(10)
    .execute()
)

if recent.data:
    st.dataframe(recent.data, use_container_width=True, hide_index=True)
else:
    st.caption("No screened candidates yet for this job.")
