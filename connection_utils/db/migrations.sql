PRAGMA foreign_keys = OFF;
DROP TABLE IF EXISTS routes_audit;
DROP TABLE IF EXISTS edges;
DROP TABLE IF EXISTS nodes;
PRAGMA foreign_keys = ON;

-- ---------- nodes ----------

CREATE TABLE IF NOT EXISTS nodes (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name   TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'published',
    CONSTRAINT nodes_name_not_blank CHECK (trim(name) <> ''),
    CONSTRAINT nodes_status_valid   CHECK (status IN ('published', 'archived'))
);

-- ---------- edges ----------


CREATE TABLE IF NOT EXISTS edges (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source      INTEGER NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    destination INTEGER NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    latency     REAL NOT NULL,
    status      TEXT NOT NULL DEFAULT 'published',
    CONSTRAINT edges_latency_positive CHECK (latency > 0),
    CONSTRAINT edges_no_self_loop     CHECK (source <> destination),
    CONSTRAINT edges_unique_pair      UNIQUE (source, destination),
    CONSTRAINT edges_status_valid     CHECK (status IN ('published', 'archived'))
);

CREATE INDEX IF NOT EXISTS idx_edges_destination ON edges (destination);

-- ---------- routes_audit ----------


CREATE TABLE IF NOT EXISTS routes_audit (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    source        TEXT NOT NULL,
    destination   TEXT NOT NULL,
    total_latency REAL NOT NULL,
    path          TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    CONSTRAINT routes_audit_latency_non_negative CHECK (total_latency >= 0),
    CONSTRAINT routes_audit_path_is_array        CHECK (json_valid(path) AND json_type(path) = 'array')
);

CREATE INDEX IF NOT EXISTS idx_routes_audit_created_at ON routes_audit (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_routes_audit_src_dst    ON routes_audit (source, destination, created_at DESC);
