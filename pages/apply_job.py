"""
pages/apply_job.py — Candidate Job Application
"""

import streamlit as st
import io
import sys
import os
import PyPDF2

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.db import get_supabase
from shared.chroma_setup import check_duplicate_resume, store_candidate_resume
from shared.ui_theme import apply_theme

apply_theme()

supabase = get_supabase()


# -------------------------------------------------
# PDF TEXT EXTRACTION
# -------------------------------------------------

def extract_pdf_text(file_bytes):
    """Extract text from a PDF file."""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception:
        return ""


# -------------------------------------------------
# HEADER
# -------------------------------------------------

st.markdown("<h1>💼 Apply for a Job</h1>", unsafe_allow_html=True)
st.caption("Submit your application — our AI reviews your profile within minutes.")
st.divider()

# -------------------------------------------------
# LOAD JOBS
# -------------------------------------------------

try:
    jobs = supabase.table("jobs").select("*").execute().data
except Exception as e:
    st.error("Database connection error")
    st.write(e)
    st.stop()

if not jobs:
    st.warning("No open positions available right now. Please check back later.")
    st.stop()

job_options = {
    f"{j['job_title']} at {j['company_name']}": j
    for j in jobs
}

# -------------------------------------------------
# TELEGRAM INSTRUCTIONS
# -------------------------------------------------

st.markdown("""
<div style='background: #13131f; border: 1px solid #2a2a3e; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;'>
    <h3 style='margin-top: 0 !important; font-size: 1.1rem !important;'>📲 Telegram Notification Setup</h3>
    <ol style='color: #a0a0c0; margin-bottom: 0.5rem;'>
        <li>Open the Telegram bot: <a href='https://t.me/talent_acq_bot' target='_blank' style='color: #6c63ff;'>t.me/talent_acq_bot</a></li>
        <li>Press <strong>/start</strong></li>
        <li>Copy your <strong>Chat ID</strong></li>
        <li>Paste it in the application form below</li>
    </ol>
    <p style='color: #7878a0; font-size: 0.85rem; margin-bottom: 0;'>
        You'll receive interview notifications directly on Telegram.
    </p>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------
# APPLICATION FORM
# -------------------------------------------------

with st.form("application_form"):

    st.subheader("👤 Personal Details")

    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("Full Name *")
        phone = st.text_input("Phone Number *")

    with col2:
        email = st.text_input("Email Address *")
        experience = st.selectbox(
            "Years of Experience",
            ["0-1 years", "1-3 years", "3-5 years", "5-10 years", "10+ years"]
        )

    st.divider()

    selected_job_label = st.selectbox(
        "Position Applying For *",
        list(job_options.keys())
    )

    selected_job = job_options[selected_job_label]

    st.divider()

    telegram_chat_id = st.text_input(
        "Telegram Chat ID",
        placeholder="Paste chat ID from Telegram bot"
    )

    st.divider()

    resume_file = st.file_uploader(
        "Upload Resume (PDF) *",
        type=["pdf"]
    )

    cover_note = st.text_area("Cover Note (Optional)")

    submitted = st.form_submit_button(
        "🚀 Submit Application", use_container_width=True
    )


# -------------------------------------------------
# FORM SUBMISSION
# -------------------------------------------------

if submitted:

    if not name or not email or not phone or not resume_file:
        st.error("Please fill all required fields.")
        st.stop()

    with st.spinner("Processing your application..."):

        try:
            # Extract resume text
            pdf_bytes = resume_file.read()
            resume_text = extract_pdf_text(pdf_bytes)

            if not resume_text:
                st.error("Could not extract text from PDF. Please upload a valid PDF resume.")
                st.stop()

            # -------------------------------------------------
            # DUPLICATE RESUME DETECTION
            # -------------------------------------------------

            if check_duplicate_resume(resume_text):
                st.error(
                    "⚠️ **Duplicate resume detected.** "
                    "A very similar resume already exists in our system. "
                    "Please submit a unique resume."
                )
                st.stop()

            # -------------------------------------------------
            # BUILD RESUME TEXT
            # -------------------------------------------------

            full_resume = (
                f"Experience: {experience}\n"
                f"Cover Note: {cover_note}\n\n"
                f"{resume_text}"
            )

            # -------------------------------------------------
            # INSERT TO SUPABASE (no screening — pipeline does that)
            # -------------------------------------------------

            result = supabase.table("candidates").insert({

                "name": name.strip(),
                "email": email.strip().lower(),
                "phone": phone.strip(),
                "telegram_chat_id": telegram_chat_id.strip() if telegram_chat_id else None,
                "job_id": selected_job["id"],
                "job_applied": selected_job_label,
                "resume_text": full_resume[:5000],
                "status": "applied",

                # Screening fields set to NULL — pipeline fills these later
                "screening_score": None,
                "screening_reason": None,
                "skills_matched": None,
                "skills_missing": None,
                "culture_fit": None,
                "recommendation": None,

            }).execute()

            # Store in ChromaDB for duplicate detection
            if result.data:
                candidate_id = result.data[0]["id"]
                store_candidate_resume(candidate_id, resume_text)

            st.success("✅ Application submitted successfully!")

            st.markdown("""
            <div style='background: #0d2b1a; border: 1px solid #166534;
                        border-radius: 12px; padding: 1.2rem; margin-top: 1rem;'>
                <div style='color: #4ade80; font-weight: 600;'>What happens next?</div>
                <div style='color: #e8e8f0; margin-top: 0.5rem; font-size: 0.9rem;'>
                    Our HR team will review your application through our AI screening pipeline.
                    If shortlisted, you'll receive a Telegram notification to schedule your interview.
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.balloons()

        except Exception as e:
            st.error("Error submitting application")
            st.write(e)
