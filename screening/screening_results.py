import streamlit as st
import sys
import os

# allow importing shared modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from shared.db import get_supabase

supabase = get_supabase()

st.set_page_config(
    page_title="Screening Results",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500&display=swap');

html, body, [class*="css"] {
font-family: 'DM Sans', sans-serif;
background: #0a0a0f;
color: #e8e8f0;
}

h1 {
font-family: 'Syne', sans-serif !important;
font-weight: 800 !important;
color: #fff !important;
}

[data-testid="metric-container"] {
background: #13131f;
border: 1px solid #2a2a3e;
border-radius: 14px;
padding: 1rem 1.2rem;
}

.stButton > button {
background: linear-gradient(135deg, #6c63ff, #a855f7) !important;
color: white !important;
border: none !important;
border-radius: 10px !important;
}

[data-testid="stSelectbox"] > div {
background: #13131f !important;
border: 1px solid #2a2a3e !important;
border-radius: 10px !important;
color: #e8e8f0 !important;
}

.main .block-container {
background: #0a0a0f;
}
</style>
""", unsafe_allow_html=True)


st.markdown("<h1>📊 Screening Results</h1>", unsafe_allow_html=True)

# Fetch jobs
jobs = supabase.table("jobs").select("id, job_title, company_name").execute().data

if not jobs:
    st.warning("No jobs posted yet.")
    st.stop()

job_map = {
    f"{j['job_title']} at {j['company_name']} (ID: {j['id']})": j["id"]
    for j in jobs
}

selected = st.selectbox("Select Job", list(job_map.keys()))
job_id = job_map[selected]

if st.button("Load Results"):

    data = (
        supabase.table("candidates")
        .select("name,email,screening_score,skills_matched,skills_missing,culture_fit,recommendation,status")
        .eq("job_id", job_id)
        .order("screening_score", desc=True)
        .execute()
    )

    candidates = data.data

    if not candidates:
        st.info("No screened candidates yet for this job.")
    else:

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Shortlisted",
            len([c for c in candidates if c["status"] == "shortlisted"])
        )

        c2.metric(
            "Maybe",
            len([c for c in candidates if c["status"] == "maybe"])
        )

        c3.metric(
            "Rejected",
            len([c for c in candidates if c["status"] == "rejected"])
        )

        st.dataframe(candidates, use_container_width=True)