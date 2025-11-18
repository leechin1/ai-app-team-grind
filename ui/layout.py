# ui/layout.py
import streamlit as st

def configure_page():
    st.set_page_config(
        page_title="Notiq - My Notes",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if 'selected_subject' not in st.session_state:
        st.session_state.selected_subject = None
    if 'selected_document' not in st.session_state:
        st.session_state.selected_document = None
    if 'show_new_subject_dialog' not in st.session_state:
        st.session_state.show_new_subject_dialog = False
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
