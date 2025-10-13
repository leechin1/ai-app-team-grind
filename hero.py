import streamlit as st
from datetime import date

# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(
    page_title="Notiq – like a studdy buddy but better",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------------
# Utilities
# -------------------------------

# Dark mode and light mode
def inject_css(theme: str = "light"):
    """Inject minimal, classy CSS inspired by Notion.
    theme: 'light' | 'dark'
    """
    light_vars = """
    :root {
        --bg: #ffffff;
        --card: #ffffff;
        --text: #111827; /* gray-900 */
        --muted: #6b7280; /* gray-500 */
        --border: #e5e7eb; /* gray-200 */
        --accent: #111827;
        --pill: #f3f4f6; /* gray-100 */
        --shadow: 0 1px 2px rgba(0,0,0,.05), 0 12px 24px rgba(0,0,0,.06);
    }
    """
    dark_vars = """
    :root {
        --bg: #0b0e14;
        --card: #0f1320;
        --text: #e5e7eb; /* gray-200 */
        --muted: #9ca3af; /* gray-400 */
        --border: #1f2937; /* gray-800 */
        --accent: #f9fafb; /* gray-50 */
        --pill: #111827; /* gray-900 */
        --shadow: 0 1px 2px rgba(0,0,0,.3), 0 12px 24px rgba(0,0,0,.2);
    }
    """

    palette = light_vars if theme == "light" else dark_vars

    st.markdown(
        f"""
        <style>
        {palette}

        html, body, [data-testid="stAppViewContainer"] {{
            background: var(--bg) !important;
            color: var(--text) !important;
        }}
        h1, h2, h3, h4, h5, h6 {{
            letter-spacing: -0.02em;
        }}
        .hero {{
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 48px 36px;
            background: var(--card);
            box-shadow: var(--shadow);
        }}
        .muted {{ color: var(--muted); }}
        .pill {{
            display: inline-flex; align-items: center; gap: 8px;
            padding: 6px 10px; border-radius: 999px;
            background: var(--pill); border: 1px solid var(--border);
            font-size: 0.875rem; font-weight: 500;
        }}
        .card {{
            border: 1px solid var(--border);
            border-radius: 16px;
            background: var(--card);
            padding: 20px; height: 100%;
            box-shadow: var(--shadow);
        }}
        .callout {{
            border: 1px solid var(--border); border-left: 4px solid var(--accent);
            padding: 16px; border-radius: 12px; background: var(--card);
        }}
        .divider {{ height: 1px; width: 100%; background: var(--border); margin: 20px 0; }}
        .footer a, .link {{ color: var(--text); text-decoration: underline; text-underline-offset: 3px; }}
        .grid {{ display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }}
        .logo-title {{ font-weight: 700; letter-spacing: -0.02em; }}
        .tiny {{ font-size: 12px; color: var(--muted); }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def header_bar():
    cols = st.columns([1, 5, 3])
    with cols[0]:
        st.markdown("### 🧩 <span class='logo-title'>Slate</span>", unsafe_allow_html=True)
    with cols[1]:
        st.write("")
    with cols[2]:
        st.markdown("<div style='text-align:right;'>Built with Streamlit · Notion‑style UI</div>", unsafe_allow_html=True)


def hero():
    st.markdown(
        """
        <div class="hero">
            <span class="pill">✨ New: Template gallery</span>
            <h1 style="margin-top: 14px; font-size: 42px;">Think in blocks. Ship in minutes.</h1>
            <p class="muted" style="max-width: 820px; font-size: 18px;">A minimalist, Notion‑inspired landing page for your next product. Clean typography, soft shadows, and block‑based sections that feel instantly familiar.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns([1, 1])
    with c1:
        st.button("🚀 Get started", use_container_width=True)
    with c2:
        st.button("📘 View Docs", use_container_width=True)


def features():
    st.markdown("### Blocks you’ll actually use")
    st.markdown('<div class="grid">', unsafe_allow_html=True)
    cards = [
        ("🧱 Blocks", "Compose sections like hero, features, FAQs, and footers with clean defaults."),
        ("🎯 Focused", "Typography‑first, neutral palette, and zero visual noise by default."),
        ("⚙️ Customizable", "Swap copy, add pages, and wire up actions without touching the CSS."),
        ("📱 Responsive", "CSS grid layout adapts to any screen size out of the box."),
        ("🌗 Themes", "Toggle light/dark from the sidebar. Uses CSS variables throughout."),
        ("🔍 SEO‑friendly", "Semantic headings and structured content (as much as Streamlit allows)."),
    ]
    for title, desc in cards:
        st.markdown(
            f"""
            <div class="card">
                <h4 style="margin:0 0 6px 0;">{title}</h4>
                <p class="muted" style="margin:0;">{desc}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)


def templates():
    st.markdown("### Template gallery")
    c1, c2, c3 = st.columns(3)
    for col, (emoji, name, blurb) in zip(
        [c1, c2, c3],
        [
            ("📄", "Startup", "Hero · Features · Social proof · CTA"),
            ("📚", "Docs", "Side nav · Headings · Code blocks"),
            ("🛠️", "Changelog", "Expander list · Badges · Dates"),
        ],
    ):
        with col:
            st.markdown(
                f"""
                <div class="card">
                    <div style="display:flex;align-items:center;gap:10px;">
                        <div style="font-size:22px;">{emoji}</div>
                        <div>
                            <div style="font-weight:600;">{name}</div>
                            <div class="tiny">{blurb}</div>
                        </div>
                    </div>
                    <div class="divider"></div>
                    <button class="pill">Use template</button>
                </div>
                """,
                unsafe_allow_html=True,
            )


def docs_page():
    st.header("📘 Documentation")
    st.markdown(
        """
        Build pages by combining sections. Each section here is a simple Python function that emits HTML/markdown blocks with shared CSS variables.
        """
    )
    with st.expander("Installation", expanded=True):
        st.code("""
        pip install streamlit
        streamlit run app.py
        """.strip(), language="bash")
    with st.expander("Layout & theming"):
        st.code(
            """
            # Toggle theme from sidebar
            theme = st.session_state.get("theme", "light")
            inject_css(theme)
            """.strip(),
            language="python",
        )
    with st.expander("Create a section"):
        st.code(
            """
            def features():
                st.markdown("### Features")
                # ... render your content
            """.strip(),
            language="python",
        )


def changelog_page():
    st.header("📝 Changelog")
    st.caption("Transparent updates for your users.")
    entries = [
        (date(2025, 10, 1), "Template gallery", "Added three starter templates with cards and actions."),
        (date(2025, 9, 20), "Dark theme", "Introduced CSS variable driven theming."),
        (date(2025, 9, 5), "Initial release", "Core Notion‑like layout with hero and features."),
    ]
    for d, title, desc in entries:
        with st.expander(f"{d.strftime('%b %d, %Y')} – {title}"):
            st.write(desc)


def templates_page():
    st.header("🧩 Templates")
    templates()


def contact_page():
    st.header("🤝 Contact")
    st.markdown(
        """
        <div class="callout">
            <strong>We’d love to hear from you.</strong><br/>
            Drop a note if you want help adapting this layout to your product.
        </div>
        """,
        unsafe_allow_html=True,
    )
    name = st.text_input("Name")
    email = st.text_input("Email")
    msg = st.text_area("Message", height=140)
    submitted = st.button("Send message")
    if submitted:
        st.success("Thanks! Your message was captured locally for this demo.")


def home_page():
    hero()
    features()
    templates()
    st.markdown("""
    <div class="divider"></div>
    <div class="footer" style="display:flex;justify-content:space-between;align-items:center;gap:16px;">
        <div class="tiny">© {year} Slate. Not affiliated with Notion.</div>
        <div class="tiny">Made with <span aria-label="love">❤️</span> & Streamlit</div>
    </div>
    """.format(year=date.today().year), unsafe_allow_html=True)


# -------------------------------
# Sidebar (Navigation & Theme)
# -------------------------------
if "theme" not in st.session_state:
    st.session_state.theme = "light"

with st.sidebar:
    st.markdown("## 🧩 Slate")
    st.caption("Notion‑like landing page")

    nav = st.radio(
        "Navigate",
        options=["Home", "Docs", "Changelog", "Templates", "Contact"],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("---")
    theme_choice = st.toggle("Dark mode", value=(st.session_state.theme == "dark"))
    st.session_state.theme = "dark" if theme_choice else "light"

# Apply CSS *after* theme is set
inject_css(st.session_state.theme)

# -------------------------------
# Render
# -------------------------------
header_bar()

if nav == "Home":
    home_page()
elif nav == "Docs":
    docs_page()
elif nav == "Changelog":
    changelog_page()
elif nav == "Templates":
    templates_page()
else:
    contact_page()
