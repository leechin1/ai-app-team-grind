# main.py
import streamlit as st
from dotenv import load_dotenv
import logging

from supabase_integration.fetching import init_supabase
from ui.layout import configure_page, init_session_state
from ui.sidebar import render_sidebar
from ui.views import render_main_view

# Load environment variables
load_dotenv()

# Initialize logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Supabase
supabase = init_supabase()

# Configure page and session
configure_page()
init_session_state()

# Sidebar can be shown only after login if you prefer. This is for production but we can hide it for now
if st.session_state.get("authenticated", False):
    render_sidebar(supabase)

render_sidebar(supabase)

render_main_view(supabase, logger)
