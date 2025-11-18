# 📁 Project Structure
your_app/
│
├─ main.py                       # App entry point + high-level routing
│
├─ ui/
│  ├─ layout.py                  # Page config + session state initialization
│  ├─ sidebar.py                 # Sidebar UI (subjects, folders, logout)
│  │
│  └─ views/
│     ├─ login_view.py           # Login screen displayed before anything else
│     ├─ document_view.py        # Display a single document
│     ├─ subject_view.py         # List documents inside a subject
│     ├─ welcome_view.py         # Home screen before selecting anything
│     └─ __init__.py             # Main UI router
│
└─ supabase_integration/
   └─ fetching.py                # All Supabase queries (data layer)

# 🔐 Authentication Flow
We added a simple login layer using placebo credentials.

Authentication is managed through st.session_state.authenticated.
When the app starts, authenticated=False.
The router first checks:
if not st.session_state.get("authenticated", False):
    render_login_view()
    st.stop()
This halts the app and displays only the login page.
After successful login, authenticated=True, unlocking the full UI.
The sidebar becomes visible only after login, preventing unauthenticated users from interacting with the app.
# 🧭 High-Level UI Routing
The router at:
ui/views/__init__.py
decides what the user sees based on session state:
Not logged in → login_view
Document selected → document_view
Subject selected → subject_view
No selection → welcome_view
This centralizes navigation logic and keeps the app organized.
# 🔄 App Flow Diagram
                          ┌─────────────────────────┐
                          │        User Opens App    │
                          └──────────────┬───────────┘
                                         │
                                         ▼
                           ┌──────────────────────────┐
                           │  Is authenticated=False? │
                           └──────────────┬───────────┘
                                         │ Yes
                                         ▼
                           ┌──────────────────────────┐
                           │       LOGIN VIEW         │
                           │  (email + password)      │
                           └──────────────┬───────────┘
                                         │ Successful login
                                         ▼
                           ┌──────────────────────────┐
                           │   Show Sidebar + Views   │
                           └──────────────┬───────────┘
                                         │
                                         ▼
                        ┌──────────────────────────────────────┐
                        │  Has selected_subject?               │
                        └──────────────┬───────────────────────┘
                                       │ Yes
                                       ▼
                        ┌──────────────────────────────────────┐
                        │         SUBJECT VIEW                 │
                        │  (list of documents in the subject)  │
                        └──────────────┬───────────────────────┘
                                       │ User selects a document
                                       ▼
                        ┌──────────────────────────────────────┐
                        │          DOCUMENT VIEW               │
                        │   (full document text + images)      │
                        └──────────────┬───────────────────────┘
                                       │ Back
                                       ▼
                        ┌──────────────────────────────────────┐
                        │         SUBJECT VIEW                 │
                        └──────────────────────────────────────┘

                                (Logout returns to Login)
# 🧱 Component Responsibilities
1. main.py
Initializes Supabase
Applies page configuration
Initializes all session variables
Renders sidebar only after login
Delegates actual UI rendering to router
2. ui/layout.py
Controls Streamlit set_page_config
Ensures all required keys exist in st.session_state
3. ui/sidebar.py
Displays subject folders
Allows users to create a new subject
Renders logout button
Hidden when user is not authenticated
4. ui/views/
Each view owns one specific page:
View	Responsibility
login_view.py	Handles login authentication
welcome_view.py	Landing screen before subject selection
subject_view.py	Lists all documents for a subject
document_view.py	Shows a document with all extracted content
The router chooses which of these to display.
# 🗂️ Data Layer (Supabase)
All database operations live inside:
1. supabase_integration/fetching.py
Responsibilities include:
Initializing Supabase client
Fetching all subjects
Fetching documents for a selected subject
Creating new subjects
Getting full document details
This keeps the UI clean and focused on rendering, not data access.