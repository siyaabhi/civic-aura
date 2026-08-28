"""
Civic Aura backend — Phase 3 starter.

Run this with:
    uvicorn main:app --reload

Then open http://127.0.0.1:8000/docs to test it in your browser.

As you complete later phases, you'll add:
- database connection (sqlite3 or SQLAlchemy) — Phase 4
- GET /localities, GET /leaderboard, POST /reports — Phase 4
- locality resolution from GPS — Phase 5
- AI moderation call — Phase 6
- duplicate detection — Phase 7
"""

import sqlite3
import os

from fastapi import FastAPI

app = FastAPI(title="Civic Aura API")

# Path to the database file — it lives in ../database/civic_aura.db relative to this file.
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "civic_aura.db")


def get_db_connection():
    """
    Opens a connection to the SQLite database.
    row_factory = sqlite3.Row means we can access columns by name (row["name"])
    instead of by position (row[1]) — much easier to read.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/")
def root():
    """Sanity check — confirms the server is alive."""
    return {"message": "Civic Aura API is running 🔥"}


@app.get("/health")
def health():
    """Used later by hosting platforms to check the server is healthy."""
    return {"status": "ok"}


@app.get("/localities")
def get_localities():
    """
    Returns every locality with its current Aura, as a list of JSON objects.
    This is the first endpoint that actually talks to the database.
    """
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT id, name, district, aura, center_lat, center_lng FROM localities ORDER BY aura DESC"
    ).fetchall()
    conn.close()

    # Convert each sqlite3.Row into a plain dict so FastAPI can turn it into JSON.
    return [dict(row) for row in rows]


@app.get("/localities/{locality_id}")
def get_locality(locality_id: int):
    """
    Returns one locality's full detail by its id.
    Try locality_id = 1, 2, or 3 in the docs page (those are your sample rows).
    """
    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM localities WHERE id = ?", (locality_id,)
    ).fetchone()
    conn.close()

    if row is None:
        return {"error": f"No locality found with id {locality_id}"}

    return dict(row)


# --- Phase 4 will add more endpoints below this line, e.g.: ---
#
# @app.post("/reports")
# @app.get("/leaderboard")