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

from fastapi import FastAPI

app = FastAPI(title="Civic Aura API")


@app.get("/")
def root():
    """Sanity check — confirms the server is alive."""
    return {"message": "Civic Aura API is running 🔥"}


@app.get("/health")
def health():
    """Used later by hosting platforms to check the server is healthy."""
    return {"status": "ok"}


# --- Phase 4 will add real endpoints below this line, e.g.: ---
#
# @app.get("/localities")
# def get_localities():
#     ...
