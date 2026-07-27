import json
import sqlite3
import uuid
from datetime import datetime, timezone

import numpy as np

from app.config import DB_PATH


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

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

-- Estado visual do no. 'validado' so pode ser setado pelo veredito da
-- mentoria (mentoria_sessions) — nunca por clique manual do usuario.
CREATE TABLE IF NOT EXISTS node_progress (
    node_id TEXT PRIMARY KEY,
    status TEXT NOT NULL CHECK (status IN ('nao_iniciado', 'lido', 'validado')) DEFAULT 'nao_iniciado',
    first_opened_at TEXT,
    validated_at TEXT,
    FOREIGN KEY (node_id) REFERENCES nodes(id)
);

CREATE TABLE IF NOT EXISTS mentoria_sessions (
    id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    veredito_validado INTEGER,
    veredito_motivo TEXT,
    FOREIGN KEY (node_id) REFERENCES nodes(id)
);

CREATE TABLE IF NOT EXISTS mentoria_turns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    turn_index INTEGER NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('mentora', 'usuario')),
    text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES mentoria_sessions(id)
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


def fetch_roadmap_graph(conn: sqlite3.Connection, roadmap_slug: str) -> tuple[list[dict], list[dict]]:
    node_rows = conn.execute(
        "SELECT id, label, roadmap_origin, description_md FROM nodes WHERE roadmap_origin = ?",
        (roadmap_slug,),
    ).fetchall()
    nodes = [
        {"id": r[0], "label": r[1], "roadmap_origin": r[2], "description_md": r[3]}
        for r in node_rows
    ]
    node_ids = {n["id"] for n in nodes}
    if not node_ids:
        return nodes, []

    placeholders = ",".join("?" for _ in node_ids)
    edge_rows = conn.execute(
        f"""
        SELECT source_id, target_id, relation_type, origin, confidence FROM edges
        WHERE source_id IN ({placeholders}) AND target_id IN ({placeholders})
        """,
        list(node_ids) * 2,
    ).fetchall()
    edges = [
        {"source_id": r[0], "target_id": r[1], "relation_type": r[2], "origin": r[3], "confidence": r[4]}
        for r in edge_rows
    ]
    return nodes, edges


def save_enrichment_results(
    conn: sqlite3.Connection,
    node_types: dict[str, str],
    new_edges: list[dict],
    embeddings: dict[str, np.ndarray],
) -> None:
    for node_id, node_type in node_types.items():
        conn.execute("UPDATE nodes SET node_type = ? WHERE id = ?", (node_type, node_id))
    for node_id, vector in embeddings.items():
        conn.execute(
            "UPDATE nodes SET embedding = ? WHERE id = ?",
            (np.asarray(vector, dtype=np.float32).tobytes(), node_id),
        )
    if new_edges:
        for e in new_edges:
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


def fetch_node(conn: sqlite3.Connection, node_id: str) -> dict | None:
    row = conn.execute(
        "SELECT id, label, roadmap_origin, description_md, node_type, generated_content FROM nodes WHERE id = ?",
        (node_id,),
    ).fetchone()
    if row is None:
        return None
    return {
        "id": row[0],
        "label": row[1],
        "roadmap_origin": row[2],
        "description_md": row[3],
        "node_type": row[4],
        "generated_content": json.loads(row[5]) if row[5] else None,
    }


def fetch_node_edges_with_labels(conn: sqlite3.Connection, node_id: str) -> tuple[list[dict], dict[str, dict]]:
    rows = conn.execute(
        "SELECT source_id, target_id, relation_type, origin, confidence FROM edges WHERE source_id = ? OR target_id = ?",
        (node_id, node_id),
    ).fetchall()
    edges = [
        {"source_id": r[0], "target_id": r[1], "relation_type": r[2], "origin": r[3], "confidence": r[4]}
        for r in rows
    ]
    neighbor_ids = {e["source_id"] for e in edges} | {e["target_id"] for e in edges}
    neighbor_ids.discard(node_id)
    node_by_id = {}
    if neighbor_ids:
        placeholders = ",".join("?" for _ in neighbor_ids)
        for r in conn.execute(
            f"SELECT id, label FROM nodes WHERE id IN ({placeholders})", list(neighbor_ids)
        ):
            node_by_id[r[0]] = {"id": r[0], "label": r[1]}
    return edges, node_by_id


def save_generated_content(conn: sqlite3.Connection, node_id: str, generated_content: dict) -> None:
    conn.execute(
        "UPDATE nodes SET generated_content = ? WHERE id = ?",
        (json.dumps(generated_content, ensure_ascii=False), node_id),
    )
    conn.commit()


def get_node_progress(conn: sqlite3.Connection, node_id: str) -> dict:
    row = conn.execute(
        "SELECT status, first_opened_at, validated_at FROM node_progress WHERE node_id = ?",
        (node_id,),
    ).fetchone()
    if row is None:
        return {"node_id": node_id, "status": "nao_iniciado", "first_opened_at": None, "validated_at": None}
    return {"node_id": node_id, "status": row[0], "first_opened_at": row[1], "validated_at": row[2]}


def mark_node_opened(conn: sqlite3.Connection, node_id: str) -> None:
    """Primeira abertura de um no: nao_iniciado -> lido. Nunca rebaixa um no
    ja 'validado' ou ja 'lido'."""
    current = get_node_progress(conn, node_id)
    if current["status"] != "nao_iniciado":
        return
    conn.execute(
        """
        INSERT INTO node_progress (node_id, status, first_opened_at)
        VALUES (?, 'lido', ?)
        ON CONFLICT(node_id) DO UPDATE SET status = 'lido', first_opened_at = excluded.first_opened_at
        WHERE node_progress.status = 'nao_iniciado'
        """,
        (node_id, _now()),
    )
    conn.commit()


def start_mentoria_session(conn: sqlite3.Connection, node_id: str) -> str:
    session_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO mentoria_sessions (id, node_id, started_at) VALUES (?, ?, ?)",
        (session_id, node_id, _now()),
    )
    conn.commit()
    return session_id


def add_mentoria_turn(conn: sqlite3.Connection, session_id: str, turn_index: int, role: str, text: str) -> None:
    conn.execute(
        "INSERT INTO mentoria_turns (session_id, turn_index, role, text, created_at) VALUES (?, ?, ?, ?, ?)",
        (session_id, turn_index, role, text, _now()),
    )
    conn.commit()


def end_mentoria_session(
    conn: sqlite3.Connection, session_id: str, node_id: str, validado: bool, motivo: str
) -> None:
    """Veredito da mentora — a UNICA forma de um no chegar a status 'validado'
    (ver skill de mentoria / especificacao, secao Interface)."""
    conn.execute(
        "UPDATE mentoria_sessions SET ended_at = ?, veredito_validado = ?, veredito_motivo = ? WHERE id = ?",
        (_now(), int(validado), motivo, session_id),
    )
    if validado:
        conn.execute(
            """
            INSERT INTO node_progress (node_id, status, validated_at)
            VALUES (?, 'validado', ?)
            ON CONFLICT(node_id) DO UPDATE SET status = 'validado', validated_at = excluded.validated_at
            """,
            (node_id, _now()),
        )
    conn.commit()


def get_mentoria_sessions_for_node(conn: sqlite3.Connection, node_id: str) -> list[dict]:
    rows = conn.execute(
        """
        SELECT id, started_at, ended_at, veredito_validado, veredito_motivo
        FROM mentoria_sessions WHERE node_id = ? ORDER BY started_at
        """,
        (node_id,),
    ).fetchall()
    return [
        {
            "id": r[0], "started_at": r[1], "ended_at": r[2],
            "veredito_validado": bool(r[3]) if r[3] is not None else None,
            "veredito_motivo": r[4],
        }
        for r in rows
    ]


def get_mentoria_turns(conn: sqlite3.Connection, session_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT turn_index, role, text, created_at FROM mentoria_turns WHERE session_id = ? ORDER BY turn_index",
        (session_id,),
    ).fetchall()
    return [{"turn_index": r[0], "role": r[1], "text": r[2], "created_at": r[3]} for r in rows]
