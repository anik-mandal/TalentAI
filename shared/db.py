from supabase import create_client
from dotenv import load_dotenv
import streamlit as st
import os

# Load environment variables (works locally with .env file)
load_dotenv()

# Propagate Streamlit Cloud secrets to os.environ for compatibility
try:
    for _k, _v in st.secrets.items():
        if isinstance(_v, str):
            os.environ.setdefault(_k, _v)
        elif hasattr(_v, "items"):
            for _sub_k, _sub_v in _v.items():
                if isinstance(_sub_v, str):
                    os.environ.setdefault(_sub_k, str(_sub_v))
except Exception:
    pass


def get_secret(key):
    """
    Get a secret from os.getenv first (local .env), then st.secrets (Streamlit Cloud).
    Supports both flat secrets and secrets under [env] section.
    """
    value = os.getenv(key)
    if value:
        return value.strip().strip('"').strip("'")
    try:
        val = st.secrets[key]
        if val is not None:
            return str(val).strip().strip('"').strip("'")
    except (KeyError, FileNotFoundError):
        pass
    try:
        val = st.secrets["env"][key]
        if val is not None:
            return str(val).strip().strip('"').strip("'")
    except (KeyError, FileNotFoundError, AttributeError):
        return None


def get_supabase():
    """
    Returns a Supabase client using credentials from .env or st.secrets
    """
    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_KEY")

    if not url or not key:
        raise Exception("Supabase credentials missing. Add them to .env (local) or Streamlit Secrets (cloud).")

    supabase = create_client(url, key)
    return supabase