# ui/sidebar.py
import streamlit as st
from supabase_integration.fetching import (
    get_subject_folders,
    create_new_subject,
    debug_cache_info,
)

def render_sidebar(supabase):
    with st.sidebar:
        st.title("📚 My Subjects")
        st.markdown("---")

        # Get all subjects
        subjects = get_subject_folders(supabase)

        if not subjects:
            st.warning("No subjects found. Create your first subject!")
        else:
            st.markdown("### 📂 Folders")
            for subject in subjects:
                if st.button(
                    f"📁 {subject}",
                    key=f"subject_{subject}",
                    use_container_width=True,
                    type="primary" if st.session_state.selected_subject == subject else "secondary"
                ):
                    st.session_state.selected_subject = subject
                    st.session_state.selected_document = None
                    st.rerun()

        st.markdown("---")

        # Debug cache info (optional)
        debug_cache_info()

        st.markdown("---")

        # New Subject Button
        if st.button("➕ New Subject", use_container_width=True, type="primary"):
            st.session_state.show_new_subject_dialog = True
            st.rerun()

        # New Subject Dialog
        if st.session_state.show_new_subject_dialog:
            _render_new_subject_dialog(supabase)
        
        st.markdown("---")

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()



def _render_new_subject_dialog(supabase):
    st.markdown("### Create New Subject")
    new_subject_name = st.text_input("Subject Name", key="new_subject_input")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Create", type="primary", use_container_width=True):
            if new_subject_name:
                success, message = create_new_subject(supabase, new_subject_name)
                if success:
                    st.success(message)
                    st.session_state.show_new_subject_dialog = False
                    st.session_state.selected_subject = new_subject_name
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.warning("Please enter a subject name")

    with col2:
        if st.button("Cancel", use_container_width=True):
            st.session_state.show_new_subject_dialog = False
            st.rerun()
