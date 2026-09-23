"""
Civic Aura backend.

Run with: uvicorn main:app --reload
Docs at:  http://127.0.0.1:8000/docs
"""

import sqlite3
import os
import math
import json
import base64

import requests
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

load_dotenv()  # reads GEMINI_API_KEY from a .env file in this folder, if present

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-3.5-flash:generateContent"
)

app = FastAPI(title="Civic Aura API")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "civic_aura.db")


def haversine_distance_km(lat1, lng1, lat2, lng2):
    """Straight-line distance between two GPS points, in kilometers."""
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def find_nearest_locality(conn, lat, lng):
    """Returns the closest locality whose radius contains this point, or None."""
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


def moderate_report(photo_url, category, is_positive):
    """
    Downloads the report's photo and asks Gemini (free tier) whether it
    plausibly shows the claimed civic behavior.
    Returns {matches, confidence, reason}. Fails safe (matches=False) on any error.
    """
    if not GEMINI_API_KEY:
        return {"matches": False, "confidence": 0.0, "reason": "No GEMINI_API_KEY set in .env"}

    try:
        image_response = requests.get(photo_url, timeout=10)
        image_response.raise_for_status()
        image_bytes = image_response.content
    except Exception as e:
        return {"matches": False, "confidence": 0.0, "reason": f"Couldn't load the photo: {e}"}

    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    behavior = "positive" if is_positive else "negative"

    prompt = (
        f"A user reported this photo as an example of {behavior} civic behavior in the "
        f"category '{category}'. Judge whether it plausibly shows that. Respond ONLY with "
        'JSON, no other text, in this exact shape: {"matches": true or false, '
        '"confidence": 0.0 to 1.0, "reason": "short reason"}'
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": image_b64}},
                ]
            }
        ]
    }

    try:
        resp = requests.post(
            GEMINI_URL,
            headers={"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        # Gemini sometimes wraps JSON in ```json fences — strip those if present.
        text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(text)
    except Exception as e:
        return {"matches": False, "confidence": 0.0, "reason": f"AI check failed: {e}"}


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class ReportIn(BaseModel):
    category: str
    is_positive: bool
    photo_url: str
    lat: float
    lng: float


@app.get("/")
def root():
    return {"message": "Civic Aura API is running 🔥"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/localities")
def get_localities():
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT id, name, district, aura, center_lat, center_lng FROM localities ORDER BY aura DESC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/localities/{locality_id}")
def get_locality(locality_id: int):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM localities WHERE id = ?", (locality_id,)).fetchone()
    conn.close()
    if row is None:
        return {"error": f"No locality found with id {locality_id}"}
    return dict(row)


@app.get("/leaderboard")
def get_leaderboard():
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
    conn = get_db_connection()

    locality = find_nearest_locality(conn, report.lat, report.lng)
    if locality is None:
        conn.close()
        return {"error": "This location isn't inside any locality we track yet."}

    ai_result = moderate_report(report.photo_url, report.category, report.is_positive)
    CONFIDENCE_THRESHOLD = 0.6

    if not ai_result.get("matches") or ai_result.get("confidence", 0) < CONFIDENCE_THRESHOLD:
        conn.execute(
            """
            INSERT INTO reports (locality_id, category, is_positive, photo_url, lat, lng, status, ai_confidence)
            VALUES (?, ?, ?, ?, ?, ?, 'rejected', ?)
            """,
            (locality["id"], report.category, report.is_positive, report.photo_url,
             report.lat, report.lng, ai_result.get("confidence", 0)),
        )
        conn.commit()
        conn.close()
        return {
            "status": "rejected",
            "reason": ai_result.get("reason", "Photo didn't match the category"),
            "message": "That ain't it chief 😭 photo doesn't match the category — try again",
        }

    cursor = conn.execute(
        """
        INSERT INTO reports (locality_id, category, is_positive, photo_url, lat, lng, status, ai_confidence)
        VALUES (?, ?, ?, ?, ?, ?, 'approved', ?)
        """,
        (locality["id"], report.category, report.is_positive, report.photo_url,
         report.lat, report.lng, ai_result.get("confidence", 0)),
    )
    report_id = cursor.lastrowid

    change = 1 if report.is_positive else -1
    new_aura = max(0, locality["aura"] + change)
    conn.execute("UPDATE localities SET aura = ? WHERE id = ?", (new_aura, locality["id"]))
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