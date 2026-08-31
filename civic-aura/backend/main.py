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
import math

from fastapi import FastAPI
from pydantic import BaseModel


class ReportIn(BaseModel):
    """
    Describes exactly what shape of data POST /reports expects.
    Notice there's no locality_id here anymore — a real phone only knows GPS
    coordinates, not which locality it's in. The backend now figures that out.
    """
    category: str
    is_positive: bool
    photo_url: str
    lat: float
    lng: float

app = FastAPI(title="Civic Aura API")

# Path to the database file — it lives in ../database/civic_aura.db relative to this file.
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "civic_aura.db")


def haversine_distance_km(lat1, lng1, lat2, lng2):
    """
    Calculates the straight-line distance between two GPS points, in kilometers.
    This is the standard formula for 'distance on a sphere' (the Earth isn't flat,
    so we can't just use normal Pythagorean distance on lat/lng).
    You don't need to understand the math deeply — just know it converts two
    (lat, lng) points into a distance in km.
    """
    R = 6371  # Earth's radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def find_nearest_locality(conn, lat, lng):
    """
    Looks at every locality, calculates how far away each one's center is from
    the given GPS point, and returns the closest one — but ONLY if that point
    actually falls within that locality's radius_km. Otherwise returns None
    (meaning: this report isn't inside any locality we track yet).
    """
    localities = conn.execute("SELECT * FROM localities").fetchall()

    best_match = None
    best_distance = None

    for loc in localities:
        distance = haversine_distance_km(lat, lng, loc["center_lat"], loc["center_lng"])
        if distance <= loc["radius_km"]:
            if best_distance is None or distance < best_distance:
                best_match = loc
                best_distance = distance

    return best_match


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
    NEW in Phase 5: figures out the locality from lat/lng automatically,
    instead of trusting a locality_id sent by the client.
    NOTE: still no AI moderation or duplicate check yet — that's Phases 6 and 7.
    """
    conn = get_db_connection()

    locality = find_nearest_locality(conn, report.lat, report.lng)
    if locality is None:
        conn.close()
        return {"error": "This location isn't inside any locality we track yet."}

    # 1. Insert the report itself, marked 'approved' for now (Phase 6 will make this conditional).
    cursor = conn.execute(
        """
        INSERT INTO reports (locality_id, category, is_positive, photo_url, lat, lng, status)
        VALUES (?, ?, ?, ?, ?, ?, 'approved')
        """,
        (locality["id"], report.category, report.is_positive, report.photo_url, report.lat, report.lng),
    )
    report_id = cursor.lastrowid

    # 2. Work out the Aura change: +1 for positive, -1 for negative, never below 0.
    change = 1 if report.is_positive else -1
    new_aura = max(0, locality["aura"] + change)

    conn.execute("UPDATE localities SET aura = ? WHERE id = ?", (new_aura, locality["id"]))

    # 3. Log the change in aura_history so we have a running record.
    conn.execute(
        "INSERT INTO aura_history (locality_id, report_id, change, new_total) VALUES (?, ?, ?, ?)",
        (locality["id"], report_id, change, new_aura),
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