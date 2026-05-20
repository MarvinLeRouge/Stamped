CREATE TABLE deleted_photos (
    file_hash   TEXT PRIMARY KEY,
    deleted_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
