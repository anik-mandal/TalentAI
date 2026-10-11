"""
app.py — TalentAI Recruitment System
Main entry point: streamlit run app.py
"""

import streamlit as st
import sys
import os

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.ui_theme import apply_theme
import subprocess

# -------------------------------------------------
# BACKGROUND BOT RUNNER
# -------------------------------------------------

@st.cache_resource
def start_telegram_bot():
    """Starts the Telegram bot in a background process if token is configured."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        try:
            bot_token = st.secrets.get("TELEGRAM_BOT_TOKEN") or st.secrets.get("env", {}).get("TELEGRAM_BOT_TOKEN")
        except Exception:
            bot_token = None

    if not bot_token or "your_" in bot_token or len(bot_token) < 10:
        return None

    try:
        bot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "engagement", "telegram_bot.py")
        env = os.environ.copy()
        env["TELEGRAM_BOT_TOKEN"] = bot_token
        process = subprocess.Popen([sys.executable, bot_path], env=env)
        return process
    except Exception as e:
        print(f"Failed to start telegram bot: {e}")
        return None

# Start bot on app load
start_telegram_bot()


# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------

st.set_page_config(
    page_title="TalentAI Recruitment System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_theme()


# -------------------------------------------------
# SESSION STATE & QUERY PARAMS SYNC
# -------------------------------------------------

# Read from query params first for persistence across reloads
portal_from_url = st.query_params.get("portal")
auth_from_url = st.query_params.get("auth") == "1"

if portal_from_url and "portal" not in st.session_state:
    st.session_state.portal = portal_from_url

if auth_from_url and "authenticated" not in st.session_state:
    st.session_state.authenticated = True

if "portal" not in st.session_state:
    st.session_state.portal = portal_from_url

if "authenticated" not in st.session_state:
    st.session_state.authenticated = auth_from_url

portal = st.session_state.portal or portal_from_url
authenticated = st.session_state.authenticated or auth_from_url


# -------------------------------------------------
# PORTAL PAGES REGISTRATION
# -------------------------------------------------

def get_hr_pages():
    """Return HR portal page definitions."""
    return [
        st.Page("pages/hr_dashboard.py", title="HR Dashboard", icon="📊", default=True),
        st.Page("pages/post_job.py", title="Post Job", icon="📝"),
        st.Page("pages/run_pipeline.py", title="Run Screening Pipeline", icon="⚙️"),
        st.Page("pages/candidate_database.py", title="Candidate Database", icon="👥"),
        st.Page("pages/screening_results.py", title="Screening Results", icon="📋"),
        st.Page("pages/scheduler_page.py", title="Interview Scheduler", icon="📅"),
        st.Page("pages/analytics_page.py", title="Analytics", icon="📈"),
    ]


def get_candidate_pages():
    """Return candidate portal page definitions."""
    return [
        st.Page("pages/apply_job.py", title="Apply for Job", icon="💼", default=True),
        st.Page("pages/chatbot_page.py", title="AI Chatbot", icon="🤖"),
        st.Page("pages/scheduler_page.py", title="Interview Scheduler", icon="📅"),
    ]


# -------------------------------------------------
# LANDING PAGE
# -------------------------------------------------

def show_landing_page():
    """Show the main landing page with portal selection."""

    st.markdown("""
    <div style='text-align: center; padding: 3rem 0 1rem 0;'>
        <h1 style='font-size: 3rem !important; margin-bottom: 0.3rem !important;'>
            🧠 TalentAI
        </h1>
        <p style='color: #7878a0; font-size: 1.2rem; margin-top: 0;'>
            AI-Powered Recruitment Platform
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")
    st.markdown("")

    col1, col_spacer, col2 = st.columns([1, 0.3, 1])

    with col1:
        st.markdown("""
        <div class='portal-card'>
            <div class='icon'>👔</div>
            <h2>HR Portal</h2>
            <p>Manage jobs, screen candidates, schedule interviews & view analytics</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Enter HR Portal", key="hr_btn", use_container_width=True):
            st.session_state.portal = "hr"
            st.query_params["portal"] = "hr"
            st.rerun()

    with col2:
        st.markdown("""
        <div class='portal-card'>
            <div class='icon'>🎯</div>
            <h2>Candidate Portal</h2>
            <p>Apply for jobs, chat with AI assistant & schedule interviews</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Enter Candidate Portal", key="cand_btn", use_container_width=True):
            st.session_state.portal = "candidate"
            st.query_params["portal"] = "candidate"
            st.rerun()

    st.markdown("""
    <div style='text-align: center; margin-top: 4rem; color: #3a3a5c; font-size: 0.85rem;'>
        Powered by Groq LLM · ChromaDB · Supabase
    </div>
    """, unsafe_allow_html=True)


# -------------------------------------------------
# HR LOGIN
# -------------------------------------------------

def show_hr_login():
    """Show HR login form."""

    st.markdown("""
    <div style='text-align: center; padding: 2rem 0 1rem 0;'>
        <h1 style='font-size: 2rem !important;'>🔐 HR Portal Login</h1>
        <p style='color: #7878a0;'>Enter your credentials to access the HR dashboard</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        with st.form("hr_login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)

        if submitted:
            if username == "admin" and password == "talentai123":
                st.session_state.authenticated = True
                st.session_state.portal = "hr"
                st.query_params["portal"] = "hr"
                st.query_params["auth"] = "1"
                st.rerun()
            else:
                st.error("❌ Invalid credentials. Please try again.")

        if st.button("← Back to Home", key="back_home_btn", use_container_width=True):
            st.session_state.portal = None
            st.session_state.authenticated = False
            st.query_params.clear()
            st.rerun()


# -------------------------------------------------
# MAIN ROUTING
# -------------------------------------------------

if portal == "hr" and authenticated:
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 1rem 0;'>
            <h2 style='font-size: 1.3rem !important; margin: 0 !important;'>🧠 TalentAI</h2>
            <p style='color: #7878a0; font-size: 0.8rem; margin: 0;'>HR Portal</p>
        </div>
        """, unsafe_allow_html=True)
        st.divider()

    nav = st.navigation(get_hr_pages())

    with st.sidebar:
        st.divider()
        if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.portal = None
            st.query_params.clear()
            st.rerun()

    nav.run()

elif portal == "candidate":
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 1rem 0;'>
            <h2 style='font-size: 1.3rem !important; margin: 0 !important;'>🧠 TalentAI</h2>
            <p style='color: #7878a0; font-size: 0.8rem; margin: 0;'>Candidate Portal</p>
        </div>
        """, unsafe_allow_html=True)
        st.divider()

    nav = st.navigation(get_candidate_pages())

    with st.sidebar:
        st.divider()
        if st.button("← Back to Home", key="cand_back_btn", use_container_width=True):
            st.session_state.portal = None
            st.session_state.authenticated = False
            st.query_params.clear()
            st.rerun()

    nav.run()

elif portal == "hr" and not authenticated:
    nav = st.navigation([st.Page(show_hr_login, title="HR Login", icon="🔐", default=True)])
    nav.run()

else:
    nav = st.navigation([st.Page(show_landing_page, title="TalentAI", icon="🧠", default=True)])
    nav.run()
