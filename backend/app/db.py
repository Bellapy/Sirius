import json
import sqlite3

from app.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    roadmap_origin TEXT NOT NULL,
    description_md TEXT,
    node_type TEXT CHECK (node_type IN ('atomic_comparable', 'atomic_conceptual', 'branch') OR node_type IS NULL),
    embedding BLOB,
    generated_content TEXT
);

CREATE TABLE IF NOT EXISTS edges (
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation_type TEXT NOT NULL CHECK (relation_type IN (
        'prerequisite_of', 'alternative_to', 'contrasts_with',
        'composes_with', 'applied_in'
    )),
    origin TEXT NOT NULL CHECK (origin IN ('roadmap', 'llm_inferred', 'manual')),
    confidence REAL NOT NULL,
    PRIMARY KEY (source_id, target_id, relation_type),
    FOREIGN KEY (source_id) REFERENCES nodes(id),
    FOREIGN KEY (target_id) REFERENCES nodes(id)
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection | None = None) -> None:
    owns_conn = conn is None
    conn = conn or get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
    if owns_conn:
        conn.close()


def upsert_roadmap(conn: sqlite3.Connection, nodes: list[dict], edges: list[dict]) -> None:
    for n in nodes:
        conn.execute(
            """
            INSERT INTO nodes (id, label, roadmap_origin, description_md, node_type, embedding, generated_content)
            VALUES (:id, :label, :roadmap_origin, :description_md, NULL, NULL, NULL)
            ON CONFLICT(id) DO UPDATE SET
                label = excluded.label,
                roadmap_origin = excluded.roadmap_origin,
                description_md = excluded.description_md
            """,
            n,
        )
    for e in edges:
        conn.execute(
            """
            INSERT INTO edges (source_id, target_id, relation_type, origin, confidence)
            VALUES (:source_id, :target_id, :relation_type, :origin, :confidence)
            ON CONFLICT(source_id, target_id, relation_type) DO UPDATE SET
                confidence = excluded.confidence
            """,
            e,
        )
    conn.commit()
