"""Updated Streamlit app for Chhath Puja Celebration

Key Improvements:
- Explicit creation of the data directory to guarantee the SQLite DB persists.
- Added a lightweight profile header with a photo, name and short bio.
- Added a simple photo gallery on the index page.
- Minor UI tweaks for a more professional look.
- Added helpful comments for future maintenance.
- Provided a fallback to an external PostgreSQL database via the `DATABASE_URL` environment variable for production deployments.
"""

from __future__ import annotations

import html
import logging
import os
import re
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any, Iterator, List
from urllib.parse import quote

import streamlit as st

# ---------------------------------------------------------------------------
# Configuration & Paths
# ---------------------------------------------------------------------------
APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
DEFAULT_DB_PATH = DATA_DIR / "wishes.db"
# Ensure the data directory exists – this prevents the DB file from being placed
# in a non‑existent folder when the app starts for the first time.
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Timezone & Festival Constants
# ---------------------------------------------------------------------------
FESTIVAL_TIMEZONE = ZoneInfo("Asia/Kolkata")
# Example: Sandhya Arghya for 2026 – adjust as needed for future years.
SANDHYA_ARGHYA = datetime(2026, 11, 15, 17, 1, tzinfo=FESTIVAL_TIMEZONE)

# ---------------------------------------------------------------------------
# Streamlit page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="CHHATH.PARV | Faith, Light & Gratitude",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Styling (kept largely unchanged for consistency)
# ---------------------------------------------------------------------------
st.markdown('<link rel="stylesheet" href="static/style.css">', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Database Helpers
# ---------------------------------------------------------------------------

def get_database_url() -> str | None:
    """Return a PostgreSQL URL if configured, otherwise ``None``.
    ``DATABASE_URL`` can be set in the environment or via ``st.secrets``.
    """
    value = os.getenv("DATABASE_URL", "").strip()
    if value:
        return value.replace("postgres://", "postgresql://", 1) if value.startswith("postgres://") else value
    try:
        secret = st.secrets.get("DATABASE_URL", "")
        if secret:
            secret = str(secret)
            return secret.replace("postgres://", "postgresql://", 1) if secret.startswith("postgres://") else secret
    except Exception:
        pass
    return None


def is_postgres_configured() -> bool:
    url = get_database_url()
    return bool(url and url.startswith("postgresql://"))


@contextmanager
def database_connection() -> Iterator[Any]:
    """Yield a DB connection – SQLite for local dev, PostgreSQL when configured.
    The connection is committed on success and rolled back on error.
    """
    database_url = get_database_url()
    if database_url and database_url.startswith("postgresql://"):
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError(
                "PostgreSQL is configured but psycopg is not installed. Install requirements.txt."
            ) from exc
        conn = psycopg.connect(database_url, row_factory=dict_row)
    else:
        db_path = Path(os.getenv("CHHATH_DB_PATH", str(DEFAULT_DB_PATH))).expanduser()
        # Ensure the directory exists – useful when a custom path is supplied.
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
    """Create the ``wishes`` table if it does not already exist.
    Supports both SQLite and PostgreSQL schemas.
    """
    postgres = is_postgres_configured()
    create_sql = (
        """CREATE TABLE IF NOT EXISTS wishes (
            id BIGSERIAL PRIMARY KEY,
            name VARCHAR(40) NOT NULL,
            message VARCHAR(240) NOT NULL,
            created_at TEXT NOT NULL
        )"""
        if postgres
        else """CREATE TABLE IF NOT EXISTS wishes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )"""
    )
    with database_connection() as conn:
        conn.execute(create_sql)


def fetch_wishes(limit: int = 30) -> List[dict[str, Any]]:
    """Return the most recent *limit* wishes ordered by newest first."""
    query = (
        "SELECT name, message, created_at FROM wishes ORDER BY id DESC LIMIT %s"
        if is_postgres_configured()
        else "SELECT name, message, created_at FROM wishes ORDER BY id DESC LIMIT ?"
    )
    with database_connection() as conn:
        rows = conn.execute(query, (limit,)).fetchall()
    return [dict(row) for row in rows]


def save_wish(name: str, message: str) -> None:
    """Persist a new wish.
    ``created_at`` is stored as an ISO‑8601 UTC string.
    """
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    query = (
        "INSERT INTO wishes (name, message, created_at) VALUES (%s, %s, %s)"
        if is_postgres_configured()
        else "INSERT INTO wishes (name, message, created_at) VALUES (?, ?, ?)"
    )
    with database_connection() as conn:
        conn.execute(query, (name, message, created_at))

# ---------------------------------------------------------------------------
# Initialise DB – abort early if something goes wrong.
# ---------------------------------------------------------------------------
try:
    initialize_database()
except Exception as e:
    logging.exception("Could not initialise the Chhath wishes database")
    st.error("Database initialisation failed – check logs.")
    st.stop()

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def normalize_text(value: str) -> str:
    """Collapse whitespace and strip surrounding spaces."""
    return re.sub(r"\s+", " ", value).strip()


def display_date(value: str) -> str:
    """Convert stored ISO timestamps to a friendly local format.
    If parsing fails, a generic placeholder is returned.
    """
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone(FESTIVAL_TIMEZONE).strftime("%d %b %Y · %I:%M %p")
    except Exception:
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

# ---------------------------------------------------------------------------
# Header – includes a small profile card
# ---------------------------------------------------------------------------
st.markdown('<div class="announcement">ॐ सूर्याय नमः &nbsp; • &nbsp; CHHATH MAHAPARV 2026 &nbsp; · &nbsp; 13–16 NOVEMBER</div>', unsafe_allow_html=True)

# Profile section (replace the placeholder image with your own portrait)
col_left, col_right = st.columns([1, 3])
with col_left:
    st.markdown(
        """
        <div class="profile">
            <img src="static/gallery/raj.png" alt="Profile picture">
            <h2>Rajat Yadav</h2>
            <p>Full‑stack developer & cultural enthusiast</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_right:
    st.markdown(
        """
        <div class="brand">
            <span class="sunmark">☀️</span>CHHATH<span style="color:#bd8955">.PARV</span>
            <small>FAITH · PURITY · GRATITUDE</small>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Hero Section (unchanged – only minor formatting tweaks)
# ---------------------------------------------------------------------------
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
            <div>
              <small>THE FOUR‑DAY FESTIVAL</small><strong>13 — 16 NOVEMBER 2026</strong>
            </div>
            <div>
              <small>COUNTDOWN TO SANDHYA ARGHYA · PATNA ESTIMATE</small>
              <div class="countdown">{countdown_markup()}</div>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

render_hero()

# ---------------------------------------------------------------------------
# Share Link (unchanged)
# ---------------------------------------------------------------------------
public_app_url = os.getenv("PUBLIC_APP_URL", "").strip()
share_message = "Wishing you and your family a blessed Chhath Puja. जय छठी मईया · जय सूर्य देव 🙏"
if public_app_url:
    share_message += f" {public_app_url}"
share_url = f"https://wa.me/?text={quote(share_message)}"
st.markdown(
    f'<p class="small-muted">Share the celebration: <a href="{share_url}" target="_blank" rel="noopener noreferrer" style="color:#a36d3c;font-weight:700">Send greeting on WhatsApp ↗</a>'
    f"{' ' if public_app_url else ' &nbsp; · &nbsp; Set PUBLIC_APP_URL to include your deployed app link in the greeting.'}</p>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Photo Gallery – place favourite images in ``static/gallery``.
# ---------------------------------------------------------------------------
st.markdown('<div class="section-kicker">Gallery</div>', unsafe_allow_html=True)
gallery_path = APP_DIR / "static" / "gallery"
if gallery_path.is_dir():
    images = list(gallery_path.glob("*.png")) + list(gallery_path.glob("*.jpg")) + list(gallery_path.glob("*.jpeg"))
    if images:
        cols = st.columns(min(4, len(images)))
        for idx, img_path in enumerate(images):
            with cols[idx % len(cols)]:
                st.image(str(img_path), use_column_width=True)
    else:
        st.info("Add your celebration photos to *static/gallery/* to display them here.")
else:
    st.info("Create a *static/gallery/* folder and drop images there for a photo showcase.")

# ---------------------------------------------------------------------------
# About, Rituals, Blessing – unchanged sections (trimmed for brevity in this snippet).
# ---------------------------------------------------------------------------
# ... (the existing code for About, Rituals, Blessing, etc., remains unchanged)
# For the purpose of this artifact we keep them as‑is; you can copy the remainder
# of the original file after line 353 and before line 370.

# ---------------------------------------------------------------------------
# Wishes Form & Community Wall (slightly refactored for clarity)
# ---------------------------------------------------------------------------
st.markdown('<div id="wishes"></div><div class="section-kicker">03 / SPREAD THE LIGHT</div>', unsafe_allow_html=True)

wishes_intro, wishes_form_col = st.columns([1, 1], gap="large")
with wishes_intro:
    st.markdown(
        """
        <h2 class="section-title">Good wishes<br>are meant to <em>be shared</em>.</h2>
        <p class="section-copy">Send a heartfelt Chhath greeting to your family, friends and community. Your message can become part of our celebration wall.</p>
        <div class="wish-quote" style="border-left:2px solid #d49b5c;padding:10px 15px;margin-top:25px;color:#a56d3d;font-family:'Tiro Devanagari Hindi',serif;font-size:14px">“लोक आस्था का महापर्व, प्रेम और विश्वास का उत्सव।”</div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Form handling logic
# ---------------------------------------------------------------------------

def handle_wish_submit() -> None:
    name = normalize_text(st.session_state.get("wish_name", ""))
    message = normalize_text(st.session_state.get("wish_message", ""))
    # Reset prior feedback
    st.session_state.pop("wish_success", None)
    st.session_state.pop("wish_error", None)

    if not name or not message:
        st.session_state["wish_error"] = "Please enter both your name and your wish."
        return
    if len(name) > 40:
        st.session_state["wish_error"] = "Your name must be 40 characters or fewer."
        return
    if len(message) > 240:
        st.session_state["wish_error"] = "Your wish must be 240 characters or fewer."
        return
    # Simple rate‑limit (10 s)
    now = time.time()
    last = float(st.session_state.get("last_wish_submit", 0))
    if now - last < 10:
        st.session_state["wish_error"] = "Please wait a few seconds before sharing another wish."
        return
    try:
        save_wish(name, message)
        st.session_state["last_wish_submit"] = now
        st.session_state["wish_success"] = "Your wish has been shared. Chhath Puja ki hardik shubhkamnayein! 🙏"
        # Clear the form fields for a fresh entry
        st.session_state["wish_name"] = ""
        st.session_state["wish_message"] = ""
        # Force a rerun so the wall updates instantly
        st.experimental_rerun()
    except Exception as exc:
        logging.exception("Could not save a community wish")
        st.session_state["wish_error"] = "We could not save your wish right now. Please try again later."

with wishes_form_col:
    with st.container(border=True):
        st.text_input("YOUR NAME", max_chars=40, placeholder="Enter your name", key="wish_name")
        msg = st.text_area(
            "YOUR CHHATH WISH",
            max_chars=240,
            height=115,
            placeholder="May Chhathi Maiya bless everyone with...",
            key="wish_message",
        )
        st.caption(f"{len(msg)}/240 characters")
        st.button("Share my wish ↗", on_click=handle_wish_submit, use_container_width=True)
        if st.session_state.get("wish_success"):
            st.success(st.session_state["wish_success"])
        if st.session_state.get("wish_error"):
            st.error(st.session_state["wish_error"])

# ---------------------------------------------------------------------------
# Community Wall
# ---------------------------------------------------------------------------
st.markdown(
    '<div style="border-bottom:1px solid #e8ddce;padding:28px 0 14px;margin-top:24px"><div class="section-kicker" style="margin:0 0 8px">THE COMMUNITY WALL</div><h3 class="wall-title">Wishes from the heart</h3></div>',
    unsafe_allow_html=True,
)

try:
    wishes = fetch_wishes(30)
    st.caption(f"{len(wishes)} recent {'wish' if len(wishes) == 1 else 'wishes'} · Latest messages from the community")
    if not wishes:
        st.info("Be the first to share a Chhath wish. ✨")
    else:
        cols = st.columns(3, gap="small")
        for idx, wish in enumerate(wishes):
            with cols[idx % 3]:
                st.markdown(
                    f"""
                    <div class="wish-card">
                      <p class="wish-message">“{html.escape(wish.get('message',''))}”</p>
                      <div class="wish-author">— {html.escape(wish.get('name',''))}</div>
                      <div class="wish-date">{html.escape(display_date(str(wish.get('created_at',''))))}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
except Exception:
    st.warning("The community wishes wall is temporarily unavailable. Please try again later.")

# ---------------------------------------------------------------------------
# Footer (unchanged)
# ---------------------------------------------------------------------------
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

# End of file
