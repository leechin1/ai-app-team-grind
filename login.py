import streamlit as st

def login_page():
    st.title("Login to Your App")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    
    if st.button("Login"):
        if check_login(username, password):  # You would define check_login based on your criteria
            st.success("Logged in successfully!")
        else:
            st.error("Invalid credentials")

def check_login(username, password):
    # Replace this with your actual login logic (database, API calls, etc.)
    return username == "admin" and password == "password"
