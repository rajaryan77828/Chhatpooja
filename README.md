# CHHATH.PARV — Streamlit Edition

A native Streamlit version of the original Chhath.PARV celebration site. It retains the festival greeting, 2026 four-day ritual guide, live Sandhya Arghya countdown, WhatsApp sharing links, and community wishes wall.

## What's changed

- Replaced the Flask application and browser JavaScript with one Streamlit app: `streamlit_app.py`.
- Replaced the `/api/wishes` HTTP endpoints with direct, validated database operations.
- Kept SQLite for simple local use and added optional PostgreSQL support for persistent cloud hosting.
- Added input length validation, whitespace normalization, parameterized SQL, escaped wish rendering, and a per-session submission cooldown.
- Added Streamlit configuration and a cloud start command.

## Run on Windows (VS Code)

Open the project folder in VS Code, then run these commands in the integrated terminal:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

If PowerShell blocks virtual-environment activation, use Command Prompt:

```bat
.venv\Scripts\activate.bat
pip install -r requirements.txt
streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

Open `http://localhost:8501` in your browser. In VS Code, open the **PORTS** panel, forward port **8501**, then open the forwarded address. Do not forward port 5000 for this Streamlit version.

## Database options

### Local / simple deployment: SQLite (default)

The app creates `data/wishes.db` automatically. You can choose another location by setting `CHHATH_DB_PATH`.

PowerShell:

```powershell
$env:CHHATH_DB_PATH = "data/wishes.db"
streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

### Cloud deployment: PostgreSQL (recommended for persistent public wishes)

Set an environment variable named `DATABASE_URL` to your PostgreSQL connection string. The app automatically uses PostgreSQL when that variable is set. `psycopg` is included in `requirements.txt`. Optionally set `PUBLIC_APP_URL` to your deployed app URL so WhatsApp greetings include the clickable site link.

For Streamlit Community Cloud, add `DATABASE_URL` in **App → Settings → Secrets**:

```toml
DATABASE_URL = "postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require"
```

Use your provider's actual connection string. Never commit credentials or `secrets.toml` to GitHub. Streamlit Community Cloud's local filesystem should not be treated as durable storage; use PostgreSQL if community wishes must survive app restarts and redeployments.

## Deploy

### Streamlit Community Cloud

1. Push this project folder to a GitHub repository.
2. In Streamlit Community Cloud, create an app from that repository.
3. Set the main file path to `streamlit_app.py`.
4. Add `DATABASE_URL` in app Secrets if you want persistent community wishes.
5. Deploy.

### Render

- Build command: `pip install -r requirements.txt`
- Start command: `streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port $PORT`
- Set `DATABASE_URL` to a managed PostgreSQL database for persistent wishes.

## Project structure

```text
chhath_puja_streamlit/
├── streamlit_app.py
├── requirements.txt
├── Procfile
├── README.md
├── .gitignore
└── .streamlit/
    └── config.toml
```

## Festival timing note

The original page's festival dates are retained: 13–16 November 2026. The live countdown targets 15 November 2026 at 5:01 PM India time as an estimate for Patna Sandhya Arghya. This is not an official panchang time; local sunrise/sunset and ritual timings vary. Confirm timings with your local panchang or Chhath samiti.

## Privacy and moderation

Wishes are public on the community wall. The app validates message lengths, uses parameterized SQL, escapes user-submitted text before rendering it as HTML, and applies a lightweight per-session cooldown. This is a small community app, not a fully moderated high-traffic publishing platform. For a larger public deployment, add persistent rate limiting, moderation/reporting, backups, and operational monitoring.
