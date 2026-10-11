import streamlit as st
import os
import sys
from dotenv import load_dotenv
from groq import Groq

# allow imports from shared
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from shared.db import get_supabase
from shared.chroma_setup import get_jobs_collection

load_dotenv()

# -----------------------------
# INITIALIZATION
# -----------------------------

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("Missing GROQ_API_KEY in .env")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

supabase = get_supabase()
chroma = get_jobs_collection()

# -----------------------------
# PAGE CONFIG
# -----------------------------

st.set_page_config(
    page_title="TalentAI HR Assistant",
    page_icon="🤖",
    layout="centered"
)

# -----------------------------
# UI STYLING
# -----------------------------

st.markdown("""
<style>

.stApp {
    background: linear-gradient(180deg,#0E1117,#0B0F16);
}

.block-container {
    max-width: 760px;
}

textarea, input {
    border-radius: 10px !important;
}

button {
    border-radius: 10px !important;
}

[data-testid="stChatMessage"] {
    border-radius: 12px;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# HEADER
# -----------------------------

st.title("🤖 TalentAI HR Assistant")
st.caption("Ask questions about your job application, interview process, or role.")

# -----------------------------
# SESSION STATE
# -----------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "candidate" not in st.session_state:
    st.session_state.candidate = None

# -----------------------------
# SIDEBAR
# -----------------------------

with st.sidebar:

    st.title("TalentAI")

    st.markdown("---")

    st.subheader("AI Recruitment Assistant")

    st.write("Ask about:")

    st.write("• Job requirements")
    st.write("• Interview preparation")
    st.write("• Role responsibilities")
    st.write("• Skills needed")

    st.markdown("---")

# -----------------------------
# EMAIL LOGIN
# -----------------------------

email = st.text_input("Enter your email")

if email and st.session_state.candidate is None:

    try:
        result = supabase.table("candidates") \
            .select("*") \
            .eq("email", email) \
            .execute()

        candidate_data = result.data

    except:
        st.error("Database connection error.")
        st.stop()

    if not candidate_data:
        st.error("Email not found in our system.")
        st.stop()

    candidate = candidate_data[0]

    score = candidate.get("source_quality_score") or 0

    if score < 5:
        st.warning("Your application is still under review.")
        st.stop()

    st.session_state.candidate = candidate

# -----------------------------
# CANDIDATE INFO
# -----------------------------

if st.session_state.candidate:

    candidate = st.session_state.candidate

    name = candidate.get("name", "Candidate")
    job_applied = candidate.get("job_applied", "Unknown Role")
    status = candidate.get("status", "unknown")

    st.success(f"Welcome {name}")

    with st.sidebar:

        st.subheader("Candidate Info")

        st.write(f"Name: {name}")
        st.write(f"Role: {job_applied}")
        st.write(f"Email: {email}")

# -----------------------------
# INTERVIEW BOOKING PROMPT
# -----------------------------

    if status in ["shortlisted", "maybe"]:

        st.markdown("---")

        st.success("🎉 You are shortlisted! You can now schedule your interview.")

        if st.button("📅 Book Interview Slot"):

            st.success(
                "👉 Open the **Scheduler page from the sidebar** to book your interview slot."
            )

# -----------------------------
# SHOW CHAT HISTORY
# -----------------------------

    for msg in st.session_state.messages:

        with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "🤖"):
            st.write(msg["content"])

# -----------------------------
# CHAT INPUT
# -----------------------------

    question = st.chat_input("Ask something about the job...")

    if question:

        st.session_state.messages.append({
            "role": "user",
            "content": question
        })

        with st.chat_message("user", avatar="👤"):
            st.write(question)

        with st.spinner("Thinking..."):

            context = ""

            try:

                results = chroma.query(
                    query_texts=[job_applied],
                    n_results=1
                )

                if results and results.get("documents"):
                    context = results["documents"][0][0]

            except:
                context = ""

            system_prompt = f"""
You are an AI HR assistant for TalentAI.

Use the job description to answer candidate questions.

JOB DETAILS:
{context}

Rules:
- Be helpful
- Be concise
- Be professional
"""

            try:

                response = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": question}
                    ],
                    temperature=0.3
                )

                answer = response.choices[0].message.content

            except Exception as e:

                answer = "Sorry, I couldn't generate a response right now."

        with st.chat_message("assistant", avatar="🤖"):
            st.write(answer)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

        try:

            supabase.table("chat_logs").insert({
                "email": email,
                "question": question,
                "answer": answer
            }).execute()

        except:
            pass