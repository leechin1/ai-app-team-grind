import streamlit as st

# ---------- SESSION STATE ----------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# ---------- LOGIN VIEW ----------
VALID_EMAIL = "test@example.com"
VALID_PASSWORD = "password123"

def render_login_view():
    st.title("🔐 Login to Notiq")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if email == VALID_EMAIL and password == VALID_PASSWORD:
            st.session_state.authenticated = True
            st.success("Logged in!")
            st.rerun()
        else:
            st.error("Invalid email or password")

# ---------- MAIN CONTENT ----------
def render_app():
    st.title("📚 Main App")
    st.write("You are logged in! 🎉")

    if st.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

# ---------- ROUTER ----------
if not st.session_state.authenticated:
    render_login_view()
    st.stop()   # IMPORTANT: stop here so app doesn't render below

render_app()
