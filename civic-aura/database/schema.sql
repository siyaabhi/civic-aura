-- Civic Aura database schema — Phase 2
-- Run with: sqlite3 civic_aura.db < schema.sql

-- Every locality in Kerala tracked by the app, with its current Aura score.
CREATE TABLE localities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,               -- e.g. "Kakkanad"
    district TEXT NOT NULL,           -- e.g. "Ernakulam"
    center_lat REAL NOT NULL,         -- used for Phase 5 GPS -> locality matching
    center_lng REAL NOT NULL,
    radius_km REAL NOT NULL DEFAULT 2.0,
    aura INTEGER NOT NULL DEFAULT 0 CHECK (aura >= 0),  -- min 0, no max
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- App users (kept simple for now — expand with auth in a later phase).
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Every civic report submitted by a user.
CREATE TABLE reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    locality_id INTEGER REFERENCES localities(id),
    category TEXT NOT NULL,           -- e.g. "littering", "clean_public_space"
    is_positive BOOLEAN NOT NULL,     -- true = +1 Aura, false = -1 Aura
    photo_url TEXT NOT NULL,
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending | approved | rejected | duplicate
    ai_confidence REAL,                -- Phase 6: how sure the AI was the photo matches the category
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Every time a locality's Aura changes, log it here.
-- This is what powers the "Aura over time" graph and also helps duplicate detection (Phase 7).
CREATE TABLE aura_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    locality_id INTEGER REFERENCES localities(id),
    report_id INTEGER REFERENCES reports(id),
    change INTEGER NOT NULL,          -- +1 or -1
    new_total INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Optional (Phase 10): community reactions on a report, e.g. "🔥" or "💀"
CREATE TABLE reactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER REFERENCES reports(id),
    emoji TEXT NOT NULL,
    count INTEGER NOT NULL DEFAULT 1
);

-- Optional (Phase 10): time-limited Civic Challenges per locality
CREATE TABLE challenges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    locality_id INTEGER REFERENCES localities(id),
    goal_description TEXT NOT NULL,   -- e.g. "Gain +50 Aura this week"
    target_aura_change INTEGER NOT NULL,
    deadline TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- A few sample localities to test with (Kochi area).
INSERT INTO localities (name, district, center_lat, center_lng, aura) VALUES
    ('Kakkanad', 'Ernakulam', 10.0159, 76.3419, 120),
    ('Edappally', 'Ernakulam', 10.0270, 76.3082, 95),
    ('Fort Kochi', 'Ernakulam', 9.9658, 76.2422, 210);
