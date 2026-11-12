from __future__ import annotations

import html
import logging
import os
import re
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import quote
from zoneinfo import ZoneInfo

import streamlit as st


# ============================================================
# CHHATH.PARV — Native Streamlit celebration application
# ============================================================

APP_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = APP_DIR / "data" / "wishes.db"
FESTIVAL_TIMEZONE = ZoneInfo("Asia/Kolkata")
SANDHYA_ARGHYA = datetime(2026, 11, 15, 17, 1, tzinfo=FESTIVAL_TIMEZONE)

st.set_page_config(
    page_title="CHHATH.PARV | Faith, Light & Gratitude",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ---------------------------- Styling ----------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,500;1,600&family=Tiro+Devanagari+Hindi&display=swap');

    :root {
      --ink: #211d32; --ink-2: #302840; --gold: #d5a15e; --gold-light: #f0c987;
      --paper: #fbf7ef; --paper-2: #f2ece2; --muted: #817985; --line: #e8ddce;
    }
    html { scroll-behavior: smooth; }
    .stApp { background: var(--paper); color: var(--ink); font-family: 'DM Sans', sans-serif; }
    [data-testid="stHeader"] { background: rgba(251,247,239,.92); }
    [data-testid="stToolbar"] { right: 1rem; }
    .block-container { max-width: 1240px; padding-top: 1.2rem; padding-bottom: 2rem; }
    #MainMenu, footer { visibility: hidden; }
    .announcement { text-align:center; background:#211d32; color:#e9c48c; padding:9px 12px; margin:-1.2rem -1rem 1.1rem; font-size:11px; letter-spacing:1.4px; }
    .topline { display:flex; align-items:center; justify-content:space-between; gap:16px; padding:6px 0 20px; border-bottom:1px solid var(--line); margin-bottom:20px; }
    .brand { color:var(--ink); font-weight:800; font-size:20px; letter-spacing:1.2px; line-height:1.05; }
    .brand .sunmark { color:var(--gold); font-size:26px; vertical-align:-2px; margin-right:8px; }
    .brand small { display:block; color:#9b8c7c; font-size:8px; letter-spacing:2px; margin:5px 0 0 37px; font-weight:600; }
    .navhint { color:#766f7a; font-size:11px; text-align:right; }
    .hero { position:relative; overflow:hidden; min-height:460px; padding:58px 5.5%; border-radius:5px; color:#fff; background:radial-gradient(ellipse at 77% 60%,#684354 0%,#35263f 34%,#211d32 73%); }
    .hero:before { content:''; position:absolute; width:520px; height:520px; border-radius:50%; right:4%; top:35px; background:radial-gradient(circle,rgba(239,177,102,.18),rgba(239,177,102,0) 68%); }
    .hero-copy { position:relative; z-index:2; max-width:590px; }
    .eyebrow { color:#e9bd7c; font-size:10px; letter-spacing:2.7px; font-weight:700; margin-bottom:22px; }
    .hindi-kicker { color:#efc98e; font-family:'Tiro Devanagari Hindi',serif; font-size:17px; margin:0 0 13px; }
    .hero h1 { color:#fff; font-family:'Playfair Display',serif; font-size:clamp(42px,5.5vw,68px); line-height:1.05; font-weight:500; letter-spacing:-1.5px; margin:0 0 18px; }
    .hero h1 em { color:#efbd76; }
    .hero-description { color:#d2c8d2; font-size:13px; line-height:1.9; max-width:470px; margin-bottom:25px; }
    .hero-note { color:#d8c6b0; font-size:10px; letter-spacing:.7px; margin-top:27px; }
    .sun-scene { position:absolute; right:4%; bottom:8%; width:42%; height:78%; min-height:290px; pointer-events:none; }
    .sun-disc { position:absolute; width:170px; height:170px; border-radius:50%; top:6%; left:38%; background:radial-gradient(circle at 40% 35%,#ffe7ad,#f4b665 62%,#d8784d); box-shadow:0 0 45px #f3b36a88,0 0 110px #e78d5d44; }
    .sun-water { position:absolute; top:58%; left:0; right:0; height:42%; background:linear-gradient(180deg,#8d5260 0%,#633e56 26%,#392c48 100%); clip-path:polygon(0 0,100% 0,100% 100%,0 100%); opacity:.85; }
    .sun-water:before { content:''; position:absolute; top:13%; left:34%; width:42%; height:72%; background:repeating-linear-gradient(180deg,#efb56b 0 2px,transparent 2px 13px); opacity:.6; filter:blur(2px); }
    .waterline { position:absolute; left:0; right:0; top:58%; height:2px; background:#efc58a; opacity:.55; }
    .ghat { position:absolute; bottom:8%; width:27%; height:31%; background:linear-gradient(145deg,#49374d,#28243c); clip-path:polygon(0 0,100% 32%,100% 100%,0 100%); }
    .ghat.left { left:0; } .ghat.right { right:0; transform:scaleX(-1); }
    .diya { position:absolute; bottom:13%; color:#ffdb91; font-size:20px; text-shadow:0 0 18px #ffb95d; }
    .diya.one { left:27%; } .diya.two { left:52%; bottom:18%; } .diya.three { right:22%; }
    .scene-caption { position:absolute; bottom:0; left:36%; color:#e8bd7e; font-size:8px; letter-spacing:2px; }
    .hero-bottom { display:flex; justify-content:space-between; align-items:end; gap:20px; margin-top:45px; padding-top:18px; border-top:1px solid #ffffff26; position:relative; z-index:2; }
    .hero-bottom small { display:block; color:#bcb0c0; font-size:8px; letter-spacing:1.8px; margin-bottom:7px; }
    .hero-bottom strong { color:#f1d2a2; font-size:11px; letter-spacing:1.4px; }
    .countdown { display:flex; gap:20px; }
    .countdown-item { min-width:44px; text-align:center; }
    .countdown-value { display:block; color:#fff; font-family:'Playfair Display',serif; font-size:25px; line-height:1; }
    .countdown-label { color:#c9bdca; display:block; font-size:8px; letter-spacing:1px; margin-top:6px; }
    .section-kicker { color:#ad7949; font-size:9px; font-weight:700; letter-spacing:2px; margin:45px 0 17px; }
    .section-title { color:var(--ink); font-family:'Playfair Display',serif; font-weight:500; font-size:clamp(30px,4vw,43px); line-height:1.14; margin:0 0 13px; }
    .section-title em { color:#b47a46; }
    .section-copy { color:#77717b; font-size:12px; line-height:1.95; }
    .value-card { background:#f5efe5; border:1px solid var(--line); padding:20px 18px; min-height:112px; }
    .value-icon { color:#bc854e; font-size:22px; margin-bottom:8px; }
    .value-name { color:#302840; font-size:12px; font-weight:700; }
    .value-desc { color:#8c838b; font-size:10px; margin-top:4px; }
    .ritual-card { height:100%; min-height:250px; padding:22px 20px; background:#f5efe5; border:1px solid #e8ddce; border-radius:3px; }
    .ritual-card.featured { background:#29243c; border-color:#29243c; }
    .ritual-num { color:#bd9468; font-family:'Playfair Display',serif; font-size:20px; text-align:right; }
    .ritual-emoji { font-size:27px; margin:0 0 15px; }
    .ritual-date { color:#a77b4b; font-size:8px; font-weight:700; letter-spacing:1.1px; }
    .ritual-card h3 { color:#302840; font-family:'Playfair Display',serif; font-size:22px; font-weight:500; margin:8px 0; }
    .ritual-card.featured h3 { color:#fff; }
    .ritual-card p { color:#77717b; font-size:10px; line-height:1.8; }
    .ritual-card.featured p { color:#c8c0ce; }
    .ritual-hindi { color:#bd8955; font-family:'Tiro Devanagari Hindi',serif; font-size:13px; margin-top:14px; }
    .timing-note { color:#8b828c; font-size:10px; line-height:1.7; margin-top:15px; }
    .blessing { text-align:center; color:#fff; padding:38px 20px; margin:45px 0 10px; background:radial-gradient(ellipse at center,#51394a,#211d32 75%); border-radius:4px; }
    .blessing-sun { color:#f1bb69; font-size:34px; text-shadow:0 0 25px #f5a54f; }
    .blessing-hindi { color:#efc98e; font-family:'Tiro Devanagari Hindi',serif; font-size:16px; margin:12px 0; }
    .blessing h2 { color:#fff; font-family:'Playfair Display',serif; font-size:clamp(27px,3.8vw,40px); font-weight:500; line-height:1.2; margin:8px 0; }
    .blessing h2 em { color:#edb96e; }
    .blessing p { color:#c5bdc8; font-size:11px; }
    .wish-panel { background:#f2ece2; border:1px solid #e8ddce; padding:22px; border-radius:4px; }
    .wish-card { background:#f5efe5; border:1px solid #e8ddce; padding:17px; min-height:125px; border-radius:3px; margin-bottom:10px; }
    .wish-message { color:#514957; font-family:'Playfair Display',serif; font-size:14px; line-height:1.7; margin:0 0 12px; overflow-wrap:anywhere; }
    .wish-author { color:#a36d3c; font-size:10px; font-weight:700; }
    .wish-date { color:#99919b; font-size:9px; margin-top:5px; }
    .wall-title { color:var(--ink); font-family:'Playfair Display',serif; font-size:25px; margin:0; }
    .footer { background:#211d32; color:#c8bfcc; padding:28px 25px; margin-top:45px; border-radius:4px; }
    .footer-brand { color:#fff; font-weight:800; letter-spacing:1px; }
    .footer-brand span { color:#e6b76e; }
    .footer-copy { font-size:10px; line-height:1.8; color:#bcb4c1; }
    .small-muted { color:#8c8490; font-size:10px; }
    div[data-testid="stForm"] { border:0; padding:0; }
    [data-testid="stVerticalBlockBorderWrapper"] { background:#f2ece2; border-color:#e8ddce !important; border-radius:4px; }
    .stTextInput label, .stTextArea label { color:#716a76 !important; font-size:10px !important; font-weight:700 !important; letter-spacing:1px !important; }
    .stTextInput input, .stTextArea textarea { background:#fffdf9 !important; border-color:#e1d6c8 !important; border-radius:2px !important; }
    .stButton button, .stFormSubmitButton button, .stLinkButton a { border-radius:2px !important; font-weight:700 !important; }
    .stFormSubmitButton button { background:#b77b43 !important; color:#fff !important; border:1px solid #b77b43 !important; }
    .stButton button[kind="secondary"] { border-color:#c9a77d !important; color:#8f6138 !important; }
    @media(max-width:800px) { .sun-scene { opacity:.38; right:-13%; width:60%; } .hero { padding:38px 6%; } .hero-bottom { align-items:flex-start; flex-direction:column; } }
    @media(max-width:520px) { .sun-scene { opacity:.22; width:90%; right:-35%; } .hero { min-height:520px; } .countdown { gap:12px; } .countdown-value { font-size:21px; } .announcement { font-size:9px; } }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------- Database ----------------------------
def get_database_url() -> str | None:
    value = os.getenv("DATABASE_URL", "").strip()
    if value:
        return value.replace("postgres://", "postgresql://", 1) if value.startswith("postgres://") else value
    try:
        secret_value = st.secrets.get("DATABASE_URL", "")
        if secret_value:
            secret_value = str(secret_value)
            return secret_value.replace("postgres://", "postgresql://", 1) if secret_value.startswith("postgres://") else secret_value
    except Exception:
        pass
    return None


def is_postgres_configured() -> bool:
    url = get_database_url()
    return bool(url and url.startswith("postgresql://"))


@contextmanager
def database_connection() -> Iterator[Any]:
    database_url = get_database_url()
    if database_url and database_url.startswith("postgresql://"):
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError("PostgreSQL is configured but psycopg is not installed. Install requirements.txt.") from exc
        conn = psycopg.connect(database_url, row_factory=dict_row)
    else:
        db_path = Path(os.getenv("CHHATH_DB_PATH", str(DEFAULT_DB_PATH))).expanduser()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path), timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=15000")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_database() -> None:
    postgres = is_postgres_configured()
    create_sql = (
        """CREATE TABLE IF NOT EXISTS wishes (
            id BIGSERIAL PRIMARY KEY,
            name VARCHAR(40) NOT NULL,
            message VARCHAR(240) NOT NULL,
            created_at TEXT NOT NULL
        )"""
        if postgres else
        """CREATE TABLE IF NOT EXISTS wishes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )"""
    )
    with database_connection() as conn:
        conn.execute(create_sql)


def fetch_wishes(limit: int = 30) -> list[dict[str, Any]]:
    with database_connection() as conn:
        rows = conn.execute(
            "SELECT name, message, created_at FROM wishes ORDER BY id DESC LIMIT %s" if is_postgres_configured()
            else "SELECT name, message, created_at FROM wishes ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def save_wish(name: str, message: str) -> None:
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    query = (
        "INSERT INTO wishes (name, message, created_at) VALUES (%s, %s, %s)"
        if is_postgres_configured()
        else "INSERT INTO wishes (name, message, created_at) VALUES (?, ?, ?)"
    )
    with database_connection() as conn:
        conn.execute(query, (name, message, created_at))


try:
    initialize_database()
except Exception as database_error:
    logging.exception("Could not initialize the Chhath wishes database")
    st.error("The wishes database could not be initialized. Check your database configuration and application logs.")
    st.stop()


# ---------------------------- Small helpers ----------------------------
def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def display_date(value: str) -> str:
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone(FESTIVAL_TIMEZONE).strftime("%d %b %Y · %I:%M %p")
    except (ValueError, TypeError):
        return "Shared with devotion"


def countdown_markup() -> str:
    now = datetime.now(FESTIVAL_TIMEZONE)
    seconds_left = max(0, int((SANDHYA_ARGHYA - now).total_seconds()))
    days, remainder = divmod(seconds_left, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    values = [(days, "DAYS"), (hours, "HOURS"), (minutes, "MINUTES"), (seconds, "SECONDS")]
    if seconds_left == 0:
        return '<div class="countdown-item"><span class="countdown-value">🙏</span><span class="countdown-label">SHUBH CHHATH</span></div>'
    return "".join(
        f'<div class="countdown-item"><span class="countdown-value">{value:02d}</span><span class="countdown-label">{label}</span></div>'
        for value, label in values
    )


# ---------------------------- Header and hero ----------------------------
st.markdown('<div class="announcement">ॐ सूर्याय नमः &nbsp; • &nbsp; CHHATH MAHAPARV 2026 &nbsp; · &nbsp; 13–16 NOVEMBER</div>', unsafe_allow_html=True)
col_brand, col_nav = st.columns([1.2, 1], vertical_alignment="center")
with col_brand:
    st.markdown('<div class="brand"><span class="sunmark">☀</span>CHHATH<span style="color:#bd8955">.PARV</span><small>FAITH · PURITY · GRATITUDE</small></div>', unsafe_allow_html=True)
with col_nav:
    st.markdown('<div class="navhint"><a href="#about" style="color:#766f7a;text-decoration:none">ABOUT</a> &nbsp; · &nbsp; <a href="#rituals" style="color:#766f7a;text-decoration:none">FOUR DAYS</a> &nbsp; · &nbsp; <a href="#wishes" style="color:#766f7a;text-decoration:none">WISHES</a><br>THE FESTIVAL OF THE SUN · Devotion · Nature · Togetherness</div>', unsafe_allow_html=True)

@st.fragment(run_every="1s")
def render_hero() -> None:
    st.markdown(
        f"""
        <section class="hero">
          <div class="hero-copy">
            <div class="eyebrow">✦ &nbsp; THE FESTIVAL OF THE SUN</div>
            <p class="hindi-kicker">जय छठी मईया · जय सूर्य देव</p>
            <h1>A festival of<br><em>faith, light</em> & gratitude.</h1>
            <p class="hero-description">May the divine light of Surya Dev and the blessings of Chhathi Maiya bring health, happiness, peace and prosperity to every home.</p>
            <div class="hero-note">— With devotion from our hearts, to yours.</div>
          </div>
          <div class="sun-scene" aria-hidden="true">
            <div class="sun-disc"></div><div class="sun-water"></div><div class="waterline"></div>
            <div class="ghat left"></div><div class="ghat right"></div>
            <div class="diya one">✦</div><div class="diya two">✦</div><div class="diya three">✦</div>
            <div class="scene-caption">THE SACRED ARGHYA</div>
          </div>
          <div class="hero-bottom">
            <div><small>THE FOUR-DAY FESTIVAL</small><strong>13 — 16 NOVEMBER 2026</strong></div>
            <div><small>COUNTDOWN TO SANDHYA ARGHYA · PATNA ESTIMATE</small><div class="countdown">{countdown_markup()}</div></div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

render_hero()


# Share link is useful on mobile and desktop; no browser API or custom JS needed.
public_app_url = os.getenv("PUBLIC_APP_URL", "").strip()
share_message = "Wishing you and your family a blessed Chhath Puja. जय छठी मईया · जय सूर्य देव 🙏"
if public_app_url:
    share_message += " " + public_app_url
share_url = f"https://wa.me/?text={quote(share_message)}"
st.markdown(f'<p class="small-muted">Share the celebration: <a href="{share_url}" target="_blank" rel="noopener noreferrer" style="color:#a36d3c;font-weight:700">Send greeting on WhatsApp ↗</a>' + ("" if public_app_url else " &nbsp; · &nbsp; Set PUBLIC_APP_URL to include your deployed app link in the greeting.") + "</p>", unsafe_allow_html=True)


# ---------------------------- About ----------------------------
st.markdown('<div id="about"></div><div class="section-kicker">01 / THE SPIRIT OF CHHATH</div>', unsafe_allow_html=True)
about_left, about_right = st.columns([1, 1.15], gap="large")
with about_left:
    st.markdown('<h2 class="section-title">A prayer to the<br><em>setting & rising Sun.</em></h2>', unsafe_allow_html=True)
with about_right:
    st.markdown('<div class="section-copy"><p>Chhath Puja is a sacred festival dedicated to Surya Dev and Chhathi Maiya. It is observed with deep devotion, discipline and gratitude, as families come together to offer Arghya to the setting and rising Sun.</p><p>More than a festival, Chhath is a beautiful expression of nature worship, inner strength, family bonds and the spirit of community.</p></div>', unsafe_allow_html=True)

values = [
    ("✺", "Devotion", "Faith in every prayer"),
    ("◉", "Purity", "Discipline in every ritual"),
    ("☼", "Gratitude", "Thankfulness for life"),
    ("♡", "Togetherness", "Strength in community"),
]
value_cols = st.columns(4, gap="small")
for col, (icon, title, desc) in zip(value_cols, values):
    with col:
        st.markdown(f'<div class="value-card"><div class="value-icon">{icon}</div><div class="value-name">{title}</div><div class="value-desc">{desc}</div></div>', unsafe_allow_html=True)


# ---------------------------- Four rituals ----------------------------
st.markdown('<div id="rituals"></div><div class="section-kicker">02 / THE SACRED JOURNEY</div>', unsafe_allow_html=True)
ritual_head, year_col = st.columns([4, 1], vertical_alignment="center")
with ritual_head:
    st.markdown('<h2 class="section-title">Four days. <em>One devotion.</em></h2><p class="section-copy">Each day carries its own meaning, preparation and prayer.</p>', unsafe_allow_html=True)
with year_col:
    st.markdown('<div style="border:1px solid #d8b98f;color:#b57c47;padding:10px;text-align:center;font-size:10px;letter-spacing:2px">CHHATH<br><b>2026</b></div>', unsafe_allow_html=True)

rituals = [
    ("01", "🌿", "FRIDAY · 13 NOVEMBER", "Nahay-Khay", "The beginning of the observance, marked by purification, cleanliness and a simple, sattvic meal.", "नहाय-खाय", False),
    ("02", "🥣", "SATURDAY · 14 NOVEMBER", "Kharna", "A day of fasting that concludes after sunset with prayers and the offering of traditional prasad.", "खरना", False),
    ("03", "🌅", "SUNDAY · 15 NOVEMBER", "Sandhya Arghya", "Devotees gather at the water's edge to offer Arghya to the setting Sun with heartfelt gratitude.", "संध्या अर्घ्य", True),
    ("04", "🌄", "MONDAY · 16 NOVEMBER", "Usha Arghya", "Prayers are offered to the rising Sun. The observance concludes with Parana and sharing prasad.", "उषा अर्घ्य एवं पारण", False),
]
ritual_cols = st.columns(4, gap="small")
for col, ritual in zip(ritual_cols, rituals):
    number, emoji, date_label, title, description, hindi, featured = ritual
    with col:
        card_class = "ritual-card featured" if featured else "ritual-card"
        st.markdown(
            f'<div class="{card_class}"><div class="ritual-num">{number}</div><div class="ritual-emoji">{emoji}</div><div class="ritual-date">{date_label}</div><h3>{title}</h3><p>{description}</p><div class="ritual-hindi">{hindi}</div></div>',
            unsafe_allow_html=True,
        )
st.markdown('<p class="timing-note">Ritual timings follow local sunrise and sunset. Please confirm the exact Arghya time with your local panchang or Chhath samiti. The countdown uses an estimated Patna Sandhya Arghya time; it is not an official panchang time.</p>', unsafe_allow_html=True)


# ---------------------------- Blessing ----------------------------
st.markdown(
    """
    <div class="blessing">
      <div class="blessing-sun">☀</div>
      <p class="blessing-hindi">छठी मईया सबके जीवन में सुख, शांति और समृद्धि दें।</p>
      <h2>May every sunrise bring<br><em>a reason to be grateful.</em></h2>
      <p>Wishing you and your loved ones a blessed Chhath Mahaparv.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

blessing_text = "छठी मईया सबके जीवन में सुख, शांति और समृद्धि दें। जय छठी मईया 🙏"
st.link_button("Share this blessing on WhatsApp ↗", f"https://wa.me/?text={quote(blessing_text)}", use_container_width=False)


# ---------------------------- Wishes form and community wall ----------------------------
st.markdown('<div id="wishes"></div><div class="section-kicker">03 / SPREAD THE LIGHT</div>', unsafe_allow_html=True)
wishes_intro, wishes_form_col = st.columns([1, 1], gap="large")
with wishes_intro:
    st.markdown('<h2 class="section-title">Good wishes<br>are meant to <em>be shared.</em></h2><p class="section-copy">Send a heartfelt Chhath greeting to your family, friends and community. Your message can become part of our celebration wall.</p><div class="wish-quote" style="border-left:2px solid #d49b5c;padding:10px 15px;margin-top:25px;color:#a56d3d;font-family:\'Tiro Devanagari Hindi\',serif;font-size:14px">“लोक आस्था का महापर्व, प्रेम और विश्वास का उत्सव।”</div>', unsafe_allow_html=True)

def handle_wish_submit() -> None:
    clean_name = normalize_text(st.session_state.get("wish_name", ""))
    clean_message = normalize_text(st.session_state.get("wish_message", ""))
    st.session_state.pop("wish_success", None)
    st.session_state.pop("wish_error", None)

    if not clean_name or not clean_message:
        st.session_state["wish_error"] = "Please enter both your name and your wish."
        return
    if len(clean_name) > 40:
        st.session_state["wish_error"] = "Your name must be 40 characters or fewer."
        return
    if len(clean_message) > 240:
        st.session_state["wish_error"] = "Your wish must be 240 characters or fewer."
        return

    now = time.time()
    last_submit = float(st.session_state.get("last_wish_submit", 0))
    if now - last_submit < 10:
        st.session_state["wish_error"] = "Please wait a few seconds before sharing another wish."
        return

    try:
        save_wish(clean_name, clean_message)
        st.session_state["last_wish_submit"] = now
        st.session_state["wish_success"] = "Your wish has been shared. Chhath Puja ki hardik shubhkamnayein! 🙏"
        st.session_state["wish_name"] = ""
        st.session_state["wish_message"] = ""
    except Exception:
        logging.exception("Could not save a community wish")
        st.session_state["wish_error"] = "We could not save your wish right now. Please try again later."


with wishes_form_col:
    with st.container(border=True):
        st.text_input("YOUR NAME", max_chars=40, placeholder="Enter your name", key="wish_name")
        wish_message_value = st.text_area("YOUR CHHATH WISH", max_chars=240, height=115, placeholder="May Chhathi Maiya bless everyone with...", key="wish_message")
        st.caption(f"{len(wish_message_value)}/240 characters")
        st.button("Share my wish ↗", on_click=handle_wish_submit, use_container_width=True)
        if st.session_state.get("wish_success"):
            st.success(st.session_state["wish_success"])
        if st.session_state.get("wish_error"):
            st.error(st.session_state["wish_error"])

st.markdown('<div style="border-bottom:1px solid #e8ddce;padding:28px 0 14px;margin-top:24px"><div class="section-kicker" style="margin:0 0 8px">THE COMMUNITY WALL</div><h3 class="wall-title">Wishes from the heart</h3></div>', unsafe_allow_html=True)
try:
    wishes = fetch_wishes(30)
    st.caption(f"{len(wishes)} recent {'wish' if len(wishes) == 1 else 'wishes'} · Latest messages from the community")
    if not wishes:
        st.info("Be the first to share a Chhath wish. ✨")
    else:
        wish_columns = st.columns(3, gap="small")
        for index, wish in enumerate(wishes):
            message_html = html.escape(str(wish.get("message", "")))
            name_html = html.escape(str(wish.get("name", "")))
            date_html = html.escape(display_date(str(wish.get("created_at", ""))))
            with wish_columns[index % 3]:
                st.markdown(
                    f'<div class="wish-card"><p class="wish-message">“{message_html}”</p><div class="wish-author">— {name_html}</div><div class="wish-date">{date_html}</div></div>',
                    unsafe_allow_html=True,
                )
except Exception:
    st.warning("The community wishes wall is temporarily unavailable. Please try again later.")


# ---------------------------- Footer ----------------------------
st.markdown(
    """
    <div class="footer">
      <div class="footer-brand"><span>☀</span> CHHATH.PARV</div>
      <p class="footer-copy">May the light of Chhathi Maiya shine upon every home.<br>FAITH · PURITY · GRATITUDE</p>
      <p class="footer-copy">© 2026 CHHATH.PARV · MADE WITH DEVOTION</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption("Community messages are publicly visible. Please do not share phone numbers, addresses, passwords, or other private information.")
