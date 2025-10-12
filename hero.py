import streamlit as st


# Remove sidebar and make layout fully wide
st.set_page_config(
    page_title="Notiq Landing Page",
    page_icon="🟦",
    layout="wide"
    #initial_sidebar_state="collapsed"  # ensures sidebar stays hidden
)


# ---------- GLOBAL STYLES ----------
st.markdown("""
<style>
/* Reset & base */
* { box-sizing: border-box; }
html, body, [data-testid="stAppViewContainer"] { height: 100%; }
body { margin: 0; font-family: poppins, system-ui, -apple-system; }

/* Hide default main menu/footer */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* !!!!!!!! [data-testid="stSidebar"] { display: none; }  hides sidebar entirely */


/* Background: soft sky with clouds */
[data-testid="stAppViewContainer"] {
  background: radial-gradient(1200px 600px at 10% 40%, rgba(180,210,255,.45) 0%, rgba(255,255,255,0) 60%),
              radial-gradient(900px 500px at 90% 30%, rgba(180,240,255,.35) 0%, rgba(255,255,255,0) 60%),
              linear-gradient(180deg, #f7fbff 0%, #ffffff 30%, #f7fbff 100%);
}

/* Top nav */
.navbar {
  position: sticky; top: 0; z-index: 100;
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 20px; margin: 4px auto; max-width: 1100px;
  backdrop-filter: blur(10px);
  background: rgba(255,255,255,.6);
  border: 1px solid rgba(0,0,0,.06);
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(0,0,0,.04);
}

/* Left cluster */
.brand { display: flex; align-items: center; gap: 10px; font-weight: 700; }
.brand .dot { width: 14px; height: 14px; border-radius: 9999px; background: #3b82f6; box-shadow: 0 0 0 4px rgba(59,130,246,.15); }
.brand span { font-size: 18px; letter-spacing: .2px; }

/* Center links */
.navlinks { display: flex; gap: 22px; align-items: center; }
.navlinks a {
  text-decoration: none; color: #0f172a; font-weight: 500; opacity: .85;
}
.navlinks a:hover { opacity: 1; }

/* Right actions */
.actions { display: flex; gap: 10px; align-items: center; }
.btn {
  display: inline-flex; align-items: center; gap: 8px;
  border-radius: 12px; padding: 8px 14px; font-weight: 600; text-decoration: none;
  border: 1px solid rgba(0,0,0,.08); background: white; color: #0f172a;
}
.btn:hover { background: #f8fafc; }
.btn.gh { background: #0f172a; color: white; }
.btn.gh:hover { background: #111827; }
.btn.ghost { background: transparent; border-color: rgba(0,0,0,.08); }

/* Announcement pill */
.announcement {
  display: inline-flex; align-items: center; gap: 10px;
  padding: 10px 14px; border-radius: 9999px; border: 1px solid rgba(0,0,0,.08);
  background: rgba(255,255,255,.65); backdrop-filter: blur(6px);
  font-weight: 600; font-size: 14px; color:#0f172a;
}
.announcement a { text-decoration: none; color: #2563eb; }
.announcement .arrow { display:inline-flex; padding-left:2px; }

/* Hero */
.hero { text-align: center; margin: 90px auto 50px; max-width: 980px; }
.hero h5 { margin: 28px 0 6px; font-size: 16px; font-weight: 700; opacity: .8; }
.hero h1 {
  font-size: clamp(36px, 6.5vw, 70px);
  line-height: 1.05; margin: 0 0 16px; letter-spacing: -0.02em;
}
.hero h1 .line2 { display:block; }
.hero p.sub {
  font-size: 18px; opacity: .85; margin: 16px auto 26px; max-width: 760px; line-height: 1.65;
}

/* CTA buttons */
.cta { display:flex; gap: 14px; justify-content:center; flex-wrap: wrap; }
.cta .primary {
  background: #0f172a; color: #fff; border: 1px solid rgba(0,0,0,.85);
  padding: 14px 18px; border-radius: 14px; font-weight: 700;
}
.cta .primary:hover { filter: brightness(1.05); }
.cta .buy {
  background: #3b82f6; color: #fff; border: 1px solid rgba(59,130,246,.65);
  padding: 14px 18px; border-radius: 14px; font-weight: 700;
}
.cta .buy:hover { filter: brightness(1.05); }

.hero small { display:block; margin-top: 10px; color:#475569; }
.hero a.alt { color:#2563eb; text-decoration:none; font-weight:600; }

/* Center column width */
.container { max-width: 1100px; margin: 0 auto; padding: 0 16px; }
</style>
""", unsafe_allow_html=True)

# ---------- NAVBAR ----------
st.markdown("""
<div class="container">
  <div class="navbar">
    <div class="brand"><span class="dot"></span><span>Like a study budy, but better</span></div>
    <div class="actions">
      <a class="btn ghost" href="#">Login</a>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------- HERO ----------
st.markdown("""
<div class="container hero">
  <h5>Like a study buddy, but better.</h5>
  <h1>Notiq.</h1>
  <p class="sub">
    DESCRIPTION OF NOTIQ
  </p>
  <div class="cta">
    <a class="buy" href="#">Get in touch!</a>
  </div>
  <small>Capstone Project 2025-2026</small>
  <div style="margin-top:14px">
    <a class="alt" href="#">Carolina, Cícero, Isaac</a>
  </div>
</div>
""", unsafe_allow_html=True)

# Spacer
st.write("")
st.write("")
