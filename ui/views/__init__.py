import streamlit as st
from .document_view import render_document_view
from .subject_view import render_subject_view
from .welcome_view import render_welcome_view
from .login_view import render_login_view


def render_main_view(supabase, logger):
    if not st.session_state.get("authenticated", False):
        render_login_view()
        st.stop()

    if st.session_state.selected_document is not None:
        render_document_view(supabase)
    elif st.session_state.selected_subject:
        render_subject_view(supabase, logger)
    else:
        render_welcome_view(supabase, logger)
