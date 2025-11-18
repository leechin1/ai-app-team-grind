import streamlit as st

# Placebo credentials (you can change these)
VALID_EMAIL = "test@example.com"
VALID_PASSWORD = "password123"

def render_login_view():
    st.title("🔐 Login to Notiq")
    st.write("Enter your credentials to access your notes.")

    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login", type="primary", use_container_width=True):
        if email == VALID_EMAIL and password == VALID_PASSWORD:
            st.session_state.authenticated = True
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid email or password")
