"""
candidate_form.py

Run:
streamlit run sourcing/candidate_form.py

Candidate Application Portal for TalentAI
"""

import streamlit as st
import os
import io
import PyPDF2
from dotenv import load_dotenv
from supabase import create_client
from groq import Groq


# -------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# -------------------------------------------------

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, ".env"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)


# -------------------------------------------------
# PDF RESUME TEXT EXTRACTION
# -------------------------------------------------

def extract_pdf_text(file_bytes: bytes) -> str:

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
# AI RESUME SCORING (GROQ)
# -------------------------------------------------

def score_resume(resume_text, job_description):

    prompt = f"""
You are an AI recruitment assistant.

Evaluate how well the candidate resume matches the job description.

JOB DESCRIPTION:
{job_description}

RESUME:
{resume_text}

Return ONLY a number between 0 and 100 representing the match score.
"""

    try:

        response = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        text = response.choices[0].message.content.strip()

        digits = "".join(filter(str.isdigit, text))

        if digits:
            score = int(digits[:3])
        else:
            score = 50

        if score > 100:
            score = 100

        return score

    except:
        return 50


# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------

st.set_page_config(
    page_title="Apply | TalentAI",
    page_icon="💼",
    layout="centered"
)


# -------------------------------------------------
# MODERN UI
# -------------------------------------------------

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background: #0a0a0f;
    color: #e8e8f0;
}

#MainMenu, footer, header {visibility:hidden;}

.main .block-container {
    padding: 2.5rem 2rem;
    max-width: 720px;
}

h1 {
    font-family: 'Syne', sans-serif !important;
    font-weight: 800 !important;
}

[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] > div,
[data-testid="stTextArea"] textarea {

    background: #13131f !important;
    border: 1px solid #2a2a3e !important;
    border-radius: 10px !important;
    color: #e8e8f0 !important;
}

.stButton > button {

    background: linear-gradient(135deg,#6c63ff,#a855f7) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    width: 100% !important;
    padding: 0.8rem !important;
}

</style>
""", unsafe_allow_html=True)


# -------------------------------------------------
# PAGE TITLE
# -------------------------------------------------

st.title("💼 Apply for a Job")
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
    st.warning("No open positions available right now.")
    st.stop()

job_options = {
    f"{j['job_title']} at {j['company_name']}": j
    for j in jobs
}


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

    # TELEGRAM

    st.subheader("📲 Telegram Notifications")

    telegram_chat_id = st.text_input(
        "Telegram Chat ID",
        placeholder="Paste chat ID from Telegram bot"
    )

    st.markdown("""
### 📲 Get your Telegram Chat ID

1️⃣ Click the button below  
2️⃣ Press **/start** in the bot  
3️⃣ The bot shows your **Chat ID**  
4️⃣ Copy and paste above
""")

    st.link_button(
        "Open Telegram Bot",
        "https://t.me/talent_acq_bot"
    )

    st.caption("Or search in Telegram: @talent_acq_bot")

    st.divider()

    resume_file = st.file_uploader(
        "Upload Resume (PDF) *",
        type=["pdf"]
    )

    cover_note = st.text_area("Cover Note (Optional)")

    submitted = st.form_submit_button("🚀 Submit Application")


# -------------------------------------------------
# FORM SUBMISSION
# -------------------------------------------------

if submitted:

    if not name or not email or not phone or not resume_file:

        st.error("Please fill all required fields.")
        st.stop()

    with st.spinner("Analyzing resume with AI..."):

        try:

            pdf_bytes = resume_file.read()
            resume_text = extract_pdf_text(pdf_bytes)

            job_description = f"""
Title: {selected_job.get("job_title")}
Skills: {selected_job.get("skills_required")}
Requirements: {selected_job.get("requirements")}
Experience: {selected_job.get("experience_years")}
"""

            score = score_resume(resume_text, job_description)

            full_resume = (
                f"Experience: {experience}\n"
                f"Cover Note: {cover_note}\n\n"
                f"{resume_text}"
            )

            supabase.table("candidates").insert({

                "name": name.strip(),
                "email": email.strip().lower(),
                "phone": phone.strip(),
                "telegram_chat_id": telegram_chat_id.strip() if telegram_chat_id else None,
                "job_id": selected_job["id"],
                "job_applied": selected_job_label,
                "resume_text": full_resume[:5000],
                "status": "applied",
                "source_quality_score": score

            }).execute()

            st.success("✅ Application submitted successfully!")
            st.success(f"🤖 AI Resume Score: {score}/100")

            st.info(
                "If shortlisted, you will receive interview notifications on Telegram."
            )

            st.balloons()

        except Exception as e:

            st.error("Error submitting application")
            st.write(e)