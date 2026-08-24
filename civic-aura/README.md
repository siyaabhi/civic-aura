# Civic Aura 🔥

A Gen-Z, crowdsourced civic-awareness platform for Kerala. Every locality has a live "Aura" score
built from real reports — report good civic behavior, it goes up; report bad behavior, it goes down.

This repo is set up so you can build it **one small piece at a time**, committing to GitHub after
each working step. You don't need to know everything up front — just do Phase 1, get it running,
commit it, then move to Phase 2.

---

## 🧠 Tech stack (chosen for what you already know: HTML/CSS + Python)

| Layer | Tool | Why |
|---|---|---|
| Backend | **Python + FastAPI** | You know Python. FastAPI is beginner-friendly, has auto docs, and is very popular. |
| Database | **SQLite** → later Postgres | SQLite is a single file, zero setup. Swap to Postgres only when you deploy for real. |
| Frontend | **Plain HTML/CSS/JS** first, React later (optional) | You already know HTML/CSS. No build tools needed to start. |
| Map | **Leaflet.js** (free, no API key needed) | Simplest way to show Kerala + locality markers. |
| AI moderation | **Anthropic Claude API** (vision) | Checks if an uploaded photo matches the selected civic category. |
| Hosting (later) | Backend: Render/Railway (free tier). Frontend: GitHub Pages/Vercel. | Free, beginner-friendly deploys. |

You don't need to install all of this today — each phase below tells you exactly what to install *when you need it*.

---

## 🧰 Phase 0 — One-time setup

1. **Install these tools** (if you don't have them):
   - [Python 3.11+](https://www.python.org/downloads/) — check with `python3 --version`
   - [Git](https://git-scm.com/downloads) — check with `git --version`
   - [VS Code](https://code.visualstudio.com/) — your code editor
2. **Create a GitHub account** at [github.com](https://github.com) if you don't have one.
3. **Create a new repository on GitHub:**
   - Click the `+` (top right) → "New repository"
   - Name it `civic-aura`
   - Keep it **Public** (or Private, your choice)
   - **Do NOT** initialize with a README (we already have one) — leave "Add README", "Add .gitignore" unchecked
   - Click "Create repository" — GitHub will show you a page with commands. Keep that tab open, you'll need the URL like `https://github.com/yourusername/civic-aura.git`

4. **Connect this local project to that GitHub repo** (run in a terminal, inside this `civic-aura` folder):
   ```bash
   git init
   git add .
   git commit -m "Initial commit: project scaffold"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/civic-aura.git
   git push -u origin main
   ```
   From now on, every time you finish a working step, you just run:
   ```bash
   git add .
   git commit -m "describe what you did"
   git push
   ```
   That's the whole Git workflow you need for this project. Commit often — after every small win, not just at the end of the day.

---

## 🗺️ The Phases (build in this order)

Each phase = one working thing you can test, then commit + push. Don't skip ahead — each phase depends on the last.

### Phase 1 — Project skeleton ✅ (already done for you in this folder)
Folders: `backend/`, `frontend/`, `database/`, `docs/`. Commit this first.

### Phase 2 — Database schema
File: `database/schema.sql` (already scaffolded — see that file).
- Run it locally to create `civic_aura.db`:
  ```bash
  cd database
  sqlite3 civic_aura.db < schema.sql
  ```
- Understand the 4 tables: `localities`, `reports`, `aura_history`, `users`. Read the comments in the file.
- **Commit:** "Add database schema"

### Phase 3 — Backend: hello world API
File: `backend/main.py` (already scaffolded with a working `/` and `/health` route).
```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```
Open `http://127.0.0.1:8000/docs` — you'll see FastAPI's auto-generated API tester. This is huge for
a beginner: you can test every endpoint from your browser without writing frontend code first.
- **Commit:** "Backend hello world with FastAPI"

### Phase 4 — Backend: connect to the database
- Add SQLAlchemy or plain `sqlite3` calls in `main.py` to read/write to `civic_aura.db`.
- Build these endpoints one at a time, testing each in `/docs` before moving to the next:
  1. `GET /localities` — list all localities + their Aura
  2. `GET /localities/{id}` — one locality's detail
  3. `POST /reports` — submit a new report (photo URL, lat/lng, category, positive/negative)
  4. `GET /leaderboard` — localities sorted by Aura
- **Commit after each endpoint works**, e.g. "Add GET /localities endpoint"

### Phase 5 — Locality resolution (GPS → locality name)
- When a report comes in with lat/lng, you need to figure out *which locality* it belongs to.
- Beginner approach: store each locality as a center point + radius in `localities` table, and pick
  the nearest one (simple distance math — no external API needed).
- Later upgrade: use a proper GeoJSON boundary file for Kerala localities (LSGD data) for accuracy.
- **Commit:** "Add locality resolution from GPS coordinates"

### Phase 6 — AI moderation (photo validation)
See `docs/ai-moderation.md` for the exact logic and prompt to send to Claude's vision API.
- Endpoint: when a report is submitted, send the photo + selected category to Claude, ask
  "does this image show [category]? yes/no + confidence".
- If yes → apply the Aura change. If no → reject with a Gen-Z-style rejection message.
- **Commit:** "Add AI image moderation for reports"

### Phase 7 — Duplicate detection
- Before applying Aura change: check `reports` table for another report in the same locality +
  same category + within the last 24 hours. If found, mark as duplicate and skip the Aura update.
- Start simple (locality + category + time window). Image-similarity matching is a stretch goal for later.
- **Commit:** "Add duplicate report detection"

### Phase 8 — Frontend: the Civic Aura Map
File: `frontend/index.html` (already scaffolded with Leaflet.js + Gen-Z styling + a demo leaderboard).
- Connect it to your backend: replace the placeholder data with real `fetch()` calls to
  `http://127.0.0.1:8000/localities` and `/leaderboard`.
- **Commit:** "Connect frontend map to backend API"

### Phase 9 — Report submission flow (photo + GPS + category)
- Add a simple form/page: file input for photo, browser Geolocation API for GPS, dropdown for category.
- Submit to `POST /reports`. Show the Gen-Z response message (see `docs/microcopy.md`) based on the result.
- **Commit:** "Add report submission form"

### Phase 10 — Community reactions + Civic Challenges
- `reactions` table (report_id, emoji, count) + endpoint to react to a report.
- `challenges` table (locality_id, goal, deadline, progress) + a simple challenge banner on the map.
- **Commit after each feature**

### Phase 11 — Polish & deploy
- Deploy backend to Render/Railway (free tier), frontend to GitHub Pages or Vercel.
- Add a proper `.env` for secrets (never commit API keys — see `.gitignore`).
- **Commit:** "Deploy v1"

---

## 📁 What's in this repo right now

```
civic-aura/
├── README.md              ← you are here
├── .gitignore
├── backend/
│   ├── main.py             (Phase 3 starter — working FastAPI app)
│   └── requirements.txt
├── database/
│   └── schema.sql          (Phase 2 starter — 4 core tables)
├── frontend/
│   └── index.html          (Phase 8 starter — styled map + leaderboard demo, static data)
└── docs/
    ├── architecture.md     (how all the pieces fit together)
    ├── ai-moderation.md    (the AI validation + duplicate detection logic)
    └── microcopy.md        (all the Gen-Z response strings, organized by event)
```

## ✅ Beginner tips

- **One phase, one commit (or several small commits within a phase).** Never let uncommitted work pile up for days.
- **Read the error message fully** before asking AI to fix it — most Python errors tell you the exact line and problem.
- **Test in `/docs`** (FastAPI's built-in tester) before wiring up the frontend — isolates bugs faster.
- **Never commit API keys.** Put them in a `.env` file (already in `.gitignore`).
- If you get stuck on a phase for more than ~30–45 min, that's a good moment to paste the exact error into an AI tool — not to skip the phase.
