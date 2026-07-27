import sqlite3

import pytest

from app.db import (
    SCHEMA,
    add_mentoria_turn,
    end_mentoria_session,
    get_mentoria_sessions_for_node,
    get_mentoria_turns,
    get_node_progress,
    mark_node_opened,
    start_mentoria_session,
    upsert_roadmap,
)


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.executescript(SCHEMA)
    upsert_roadmap(c, [{"id": "n1", "label": "No 1", "roadmap_origin": "r", "description_md": None}], [])
    return c


def test_get_node_progress_defaults_to_nao_iniciado(conn):
    progress = get_node_progress(conn, "n1")
    assert progress["status"] == "nao_iniciado"
    assert progress["first_opened_at"] is None


def test_mark_node_opened_transitions_to_lido(conn):
    mark_node_opened(conn, "n1")
    progress = get_node_progress(conn, "n1")
    assert progress["status"] == "lido"
    assert progress["first_opened_at"] is not None


def test_mark_node_opened_is_idempotent(conn):
    mark_node_opened(conn, "n1")
    first_opened = get_node_progress(conn, "n1")["first_opened_at"]
    mark_node_opened(conn, "n1")
    second = get_node_progress(conn, "n1")
    assert second["status"] == "lido"
    assert second["first_opened_at"] == first_opened


def test_mark_node_opened_never_downgrades_validado(conn):
    session_id = start_mentoria_session(conn, "n1")
    end_mentoria_session(conn, session_id, "n1", validado=True, motivo="entendeu bem")
    assert get_node_progress(conn, "n1")["status"] == "validado"

    mark_node_opened(conn, "n1")
    assert get_node_progress(conn, "n1")["status"] == "validado"


def test_mentoria_session_turns_are_ordered(conn):
    session_id = start_mentoria_session(conn, "n1")
    add_mentoria_turn(conn, session_id, 0, "mentora", "pergunta 1?")
    add_mentoria_turn(conn, session_id, 1, "usuario", "resposta 1")
    add_mentoria_turn(conn, session_id, 2, "mentora", "pergunta 2?")

    turns = get_mentoria_turns(conn, session_id)
    assert [t["role"] for t in turns] == ["mentora", "usuario", "mentora"]
    assert [t["turn_index"] for t in turns] == [0, 1, 2]


def test_end_mentoria_session_validado_false_does_not_set_validado(conn):
    session_id = start_mentoria_session(conn, "n1")
    end_mentoria_session(conn, session_id, "n1", validado=False, motivo="resposta decorada")

    assert get_node_progress(conn, "n1")["status"] == "nao_iniciado"

    sessions = get_mentoria_sessions_for_node(conn, "n1")
    assert len(sessions) == 1
    assert sessions[0]["veredito_validado"] is False
    assert sessions[0]["veredito_motivo"] == "resposta decorada"


def test_multiple_sessions_accumulate_for_node(conn):
    s1 = start_mentoria_session(conn, "n1")
    end_mentoria_session(conn, s1, "n1", validado=False, motivo="tentativa 1")
    s2 = start_mentoria_session(conn, "n1")
    end_mentoria_session(conn, s2, "n1", validado=True, motivo="tentativa 2, ok")

    sessions = get_mentoria_sessions_for_node(conn, "n1")
    assert len(sessions) == 2
    assert get_node_progress(conn, "n1")["status"] == "validado"
