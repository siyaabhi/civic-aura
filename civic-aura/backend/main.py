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
from pydantic import BaseModel


class ReportIn(BaseModel):
    """
    Describes exactly what shape of data POST /reports expects.
    FastAPI uses this to auto-validate incoming requests — if someone sends
    the wrong type (e.g. text instead of a number for lat), it rejects it
    automatically before your code even runs.
    """
    locality_id: int
    category: str
    is_positive: bool
    photo_url: str
    lat: float
    lng: float

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


@app.get("/leaderboard")
def get_leaderboard():
    """
    Returns localities ranked highest Aura first, with a 'rank' number added.
    This is what will power the leaderboard UI in the frontend.
    """
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT id, name, district, aura FROM localities ORDER BY aura DESC"
    ).fetchall()
    conn.close()

    leaderboard = []
    for rank, row in enumerate(rows, start=1):
        entry = dict(row)
        entry["rank"] = rank
        leaderboard.append(entry)

    return leaderboard


@app.post("/reports")
def create_report(report: ReportIn):
    """
    Saves a new report and updates the locality's Aura.
    NOTE: no AI moderation or duplicate check yet — that comes in Phases 6 and 7.
    For now this just proves the full read-and-write cycle works end to end.
    """
    conn = get_db_connection()

    # Make sure the locality actually exists before we do anything else.
    locality = conn.execute(
        "SELECT * FROM localities WHERE id = ?", (report.locality_id,)
    ).fetchone()
    if locality is None:
        conn.close()
        return {"error": f"No locality found with id {report.locality_id}"}

    # 1. Insert the report itself, marked 'approved' for now (Phase 6 will make this conditional).
    cursor = conn.execute(
        """
        INSERT INTO reports (locality_id, category, is_positive, photo_url, lat, lng, status)
        VALUES (?, ?, ?, ?, ?, ?, 'approved')
        """,
        (report.locality_id, report.category, report.is_positive, report.photo_url, report.lat, report.lng),
    )
    report_id = cursor.lastrowid

    # 2. Work out the Aura change: +1 for positive, -1 for negative, never below 0.
    change = 1 if report.is_positive else -1
    new_aura = max(0, locality["aura"] + change)

    conn.execute("UPDATE localities SET aura = ? WHERE id = ?", (new_aura, report.locality_id))

    # 3. Log the change in aura_history so we have a running record.
    conn.execute(
        "INSERT INTO aura_history (locality_id, report_id, change, new_total) VALUES (?, ?, ?, ?)",
        (report.locality_id, report_id, change, new_aura),
    )

    conn.commit()
    conn.close()

    return {
        "report_id": report_id,
        "locality": locality["name"],
        "change": change,
        "new_aura": new_aura,
        "message": "W report 🔥 Aura updated" if report.is_positive else "Nah bro… that's an L 💀 −1 Aura",
    }