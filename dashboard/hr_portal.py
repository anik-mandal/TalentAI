import plotly.express as px
import streamlit as st
import pandas as pd
from datetime import datetime, date
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from shared.db import get_supabase
from shared.chroma_setup import get_jobs_collection

supabase = get_supabase()
chroma_collection = get_jobs_collection()

st.set_page_config(page_title="TalentAI HR Dashboard", layout="wide")

# -------------------------
# MODERN UI STYLE
# -------------------------

st.markdown("""
<style>

.main {
    background: linear-gradient(180deg,#0E1117,#0B0F16);
}

.block-container{
    padding-top:2rem;
}

.metric-card {
    background:#11161c;
    padding:18px;
    border-radius:12px;
    border:1px solid #1f2937;
}

</style>
""", unsafe_allow_html=True)

st.title("🧠 TalentAI Recruitment Dashboard")

# -------------------------
# LOAD DATA
# -------------------------

jobs = supabase.table("jobs").select("*").execute().data or []
candidates = supabase.table("candidates").select("*").execute().data or []
slots = supabase.table("interview_slots").select("*").execute().data or []

jobs_df = pd.DataFrame(jobs)
candidates_df = pd.DataFrame(candidates)
slots_df = pd.DataFrame(slots)

# -------------------------
# GLOBAL METRICS
# -------------------------

st.subheader("Platform Overview")

total_jobs = len(jobs_df)
total_candidates = len(candidates_df)

scheduled_interviews = len(slots_df[slots_df["is_booked"] == True]) if not slots_df.empty else 0
open_slots = len(slots_df[slots_df["is_booked"] == False]) if not slots_df.empty else 0

col1,col2,col3,col4 = st.columns(4)

col1.metric("Open Positions", total_jobs)
col2.metric("Total Candidates", total_candidates)
col3.metric("Scheduled Interviews", scheduled_interviews)
col4.metric("Available Slots", open_slots)

# -------------------------
# COMPANY ANALYTICS
# -------------------------

st.subheader("Company Wise Hiring")

if not jobs_df.empty:

    company_jobs = jobs_df.groupby("company_name").size().reset_index(name="jobs")

    fig = px.bar(
        company_jobs,
        x="company_name",
        y="jobs",
        title="Jobs Posted per Company"
    )

    st.plotly_chart(fig, use_container_width=True)

# -------------------------
# JOB PIPELINE ANALYTICS
# -------------------------

st.subheader("Hiring Funnel")

if not candidates_df.empty:

    applied = len(candidates_df[candidates_df["status"] == "applied"])
    shortlisted = len(candidates_df[candidates_df["status"] == "shortlisted"])
    rejected = len(candidates_df[candidates_df["status"] == "rejected"])
    maybe = len(candidates_df[candidates_df["status"] == "maybe"])

    funnel_data = {
        "Stage": ["Applied","Shortlisted","Maybe","Rejected"],
        "Count": [applied,shortlisted,maybe,rejected]
    }

    fig = px.funnel(funnel_data, x="Count", y="Stage")

    st.plotly_chart(fig,use_container_width=True)

# -------------------------
# CANDIDATE STATUS CHART
# -------------------------

st.subheader("Candidate Status Distribution")

if not candidates_df.empty:

    status_counts = candidates_df["status"].value_counts().reset_index()
    status_counts.columns = ["Status","Count"]

    fig = px.pie(status_counts, names="Status", values="Count")

    st.plotly_chart(fig, use_container_width=True)

# -------------------------
# TOP CANDIDATES
# -------------------------

st.subheader("Top AI Ranked Candidates")

if not candidates_df.empty:

    top = candidates_df.sort_values(
        by="screening_score",
        ascending=False
    ).head(10)

    st.dataframe(
        top[[
            "name",
            "job_applied",
            "screening_score",
            "skills_matched",
            "recommendation"
        ]]
    )

# -------------------------
# JOB MANAGEMENT
# -------------------------

tabs = st.tabs([
"Post Job",
"Candidate Database",
"Interview Schedule",
"Create Interview Slots"
])

# -------------------------
# POST JOB
# -------------------------

with tabs[0]:

    st.header("Post New Job")

    with st.form("job_form"):

        col1,col2 = st.columns(2)

        with col1:
            company_name = st.text_input("Company")
            job_title = st.text_input("Role")
            location = st.text_input("Location")
            salary_range = st.text_input("Salary Range")

        with col2:
            experience = st.selectbox(
                "Experience",
                ["0-1 years","1-3 years","3-5 years","5+ years"]
            )

            skills_required = st.text_area("Required Skills")
            requirements = st.text_area("Job Description")

        submit = st.form_submit_button("Create Job")

    if submit:

        job_data = {
            "company_name": company_name,
            "job_title": job_title,
            "skills_required": skills_required,
            "requirements": requirements,
            "experience_years": experience,
            "location": location,
            "salary_range": salary_range,
            "created_at": datetime.now().isoformat()
        }

        supabase.table("jobs").insert(job_data).execute()

        job_doc = f"""
Company: {company_name}
Job: {job_title}
Skills: {skills_required}
Requirements: {requirements}
"""

        chroma_collection.add(
            documents=[job_doc],
            ids=[f"{company_name}_{job_title}_{datetime.now().timestamp()}"]
        )

        st.success("Job created successfully!")

# -------------------------
# CANDIDATE DATABASE
# -------------------------

with tabs[1]:

    st.header("Candidate Database")

    if candidates_df.empty:
        st.info("No candidates yet")
    else:

        search = st.text_input("Search candidate")

        if search:
            filtered = candidates_df[
                candidates_df["name"].str.contains(search, case=False)
            ]
        else:
            filtered = candidates_df

        st.dataframe(filtered)

# -------------------------
# INTERVIEW SCHEDULE
# -------------------------

with tabs[2]:

    st.header("Scheduled Interviews")

    booked = slots_df[slots_df["is_booked"] == True] if not slots_df.empty else []

    if len(booked) == 0:
        st.info("No interviews scheduled")
    else:

        st.dataframe(booked)

# -------------------------
# CREATE SLOTS
# -------------------------

with tabs[3]:

    st.header("Create Interview Slots")

    with st.form("slots"):

        interviewer = st.text_input("Interviewer")

        interview_date = st.date_input("Date", min_value=date.today())

        times = st.multiselect(
            "Time slots",
            ["10:00 AM","11:00 AM","12:00 PM","2:00 PM","3:00 PM","4:00 PM"]
        )

        submit = st.form_submit_button("Create Slots")

    if submit:

        for t in times:

            slot = {
                "date": str(interview_date),
                "time": t,
                "interviewer_name": interviewer,
                "is_booked": False,
                "candidate_id": None,
                "candidate_name": None,
                "created_at": datetime.now().isoformat()
            }

            supabase.table("interview_slots").insert(slot).execute()

        st.success("Slots created successfully")