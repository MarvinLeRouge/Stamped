-- Initial schema — Stamped v1

CREATE TABLE quests (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT,
    auto_name    TEXT NOT NULL,
    started_at   TEXT,
    ended_at     TEXT,
    photo_count  INTEGER NOT NULL DEFAULT 0,
    has_gpx      INTEGER NOT NULL DEFAULT 0,
    bbox_lat_min REAL,
    bbox_lat_max REAL,
    bbox_lon_min REAL,
    bbox_lon_max REAL,
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_quests_started_at ON quests(started_at);

CREATE TABLE photos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path       TEXT NOT NULL UNIQUE,
    thumb_path      TEXT,
    file_hash       TEXT NOT NULL UNIQUE,
    captured_at     TEXT,
    captured_at_src TEXT CHECK(captured_at_src IN ('exif','gpx_interp','manual','unknown')),
    lat             REAL,
    lon             REAL,
    alt             REAL,
    alt_src         TEXT CHECK(alt_src IN ('exif','gpx','api','none')),
    camera_make     TEXT,
    camera_model    TEXT,
    quest_id        INTEGER REFERENCES quests(id) ON DELETE SET NULL,
    is_orphan       INTEGER NOT NULL DEFAULT 0,
    thumb_status    TEXT NOT NULL DEFAULT 'pending'
                    CHECK(thumb_status IN ('pending','generating','done','error')),
    indexed_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_photos_captured_at  ON photos(captured_at);
CREATE INDEX idx_photos_lat_lon      ON photos(lat, lon);
CREATE INDEX idx_photos_quest        ON photos(quest_id);
CREATE INDEX idx_photos_orphan       ON photos(is_orphan);
CREATE INDEX idx_photos_thumb_status ON photos(thumb_status);

CREATE TABLE gpx_files (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path         TEXT NOT NULL UNIQUE,
    file_hash         TEXT NOT NULL UNIQUE,
    recorded_at_start TEXT,
    recorded_at_end   TEXT,
    quest_id          INTEGER REFERENCES quests(id) ON DELETE SET NULL,
    point_count       INTEGER,
    total_distance_m  REAL,
    elevation_gain_m  REAL,
    imported_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE gpx_trackpoints (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    gpx_file_id INTEGER NOT NULL REFERENCES gpx_files(id) ON DELETE CASCADE,
    recorded_at TEXT NOT NULL,
    lat         REAL NOT NULL,
    lon         REAL NOT NULL,
    alt         REAL
);

CREATE INDEX idx_trackpoints_gpx_file    ON gpx_trackpoints(gpx_file_id);
CREATE INDEX idx_trackpoints_recorded_at ON gpx_trackpoints(recorded_at);

CREATE TABLE geocode_cache (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    lat_rounded REAL NOT NULL,
    lon_rounded REAL NOT NULL,
    place_name  TEXT NOT NULL,
    queried_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(lat_rounded, lon_rounded)
);

CREATE TABLE system_state (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
