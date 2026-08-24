# Civic Aura — Architecture

## The report lifecycle (what happens after someone hits Submit)

```
User opens app
     │
     ▼
Takes photo + app grabs GPS + user picks category (e.g. "littering")
     │
     ▼
POST /reports  ──────────────►  Backend (FastAPI)
     │
     ▼
1. Locality resolution
   - Compare lat/lng to each row in `localities`
   - Pick nearest locality within its radius_km
     │
     ▼
2. Duplicate check
   - Query `reports` for same locality + category + is_positive
     within the last 24 hours
   - If found → mark status = 'duplicate', stop here, return
     the "already reported" message
     │
     ▼
3. AI moderation (Claude vision)
   - Send the photo + category to Claude
   - Ask: "does this image plausibly show <category>? yes/no + confidence"
   - If no → status = 'rejected', return rejection message
   - If yes → continue
     │
     ▼
4. Apply Aura change
   - +1 if is_positive, -1 if not (never below 0)
   - Update `localities.aura`
   - Insert a row into `aura_history`
     │
     ▼
5. Return the Gen-Z response message to the app
   (see docs/microcopy.md)
     │
     ▼
Frontend map + leaderboard re-fetch and show the new Aura
```

## Why this order?

Cheapest/fastest checks run first, so you don't waste an AI API call on something that would've
been rejected anyway:
1. Locality resolution is just math — free, instant.
2. Duplicate check is a database query — free, instant.
3. AI moderation is the only step that costs money/time — run it last, only when needed.

## Components

- **Frontend** (`frontend/`): static HTML/CSS/JS. Talks to the backend only over HTTP (`fetch`).
  Knows nothing about the database directly — this separation makes it easy to swap to
  React/mobile later without touching the backend.
- **Backend** (`backend/`): FastAPI app. Owns all business logic — Aura math, duplicate rules,
  AI calls. This is the only thing that talks to the database.
- **Database** (`database/`): SQLite file for development. The schema (`schema.sql`) is the
  source of truth for what data looks like.

## Scaling later (not needed for v1)

- SQLite → Postgres when you have real concurrent users.
- Simple radius-based locality matching → real GeoJSON boundary polygons (Kerala LSGD data) for
  accuracy at ward/panchayat level.
- Add authentication (so `user_id` on reports is real, not just a placeholder).
- Add image hashing (e.g. perceptual hash) for real image-similarity duplicate detection, not
  just "same locality + category + time window."
