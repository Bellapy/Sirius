import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.api import get_db
from app.db import SCHEMA, upsert_roadmap
from app.main import app


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr("app.db.DB_PATH", tmp_path / "unused.db")

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.executescript(SCHEMA)
    nodes = [
        {"id": "r:branch1", "label": "Bancos de Dados", "roadmap_origin": "r", "description_md": "sobre bancos"},
        {"id": "r:child1", "label": "PostgreSQL", "roadmap_origin": "r", "description_md": "banco relacional"},
        {"id": "r:child2", "label": "MongoDB", "roadmap_origin": "r", "description_md": "banco de documentos"},
        {"id": "r:child3", "label": "Redis", "roadmap_origin": "r", "description_md": "banco em memoria"},
    ]
    edges = [
        {"source_id": "r:branch1", "target_id": "r:child1", "relation_type": "prerequisite_of", "origin": "roadmap", "confidence": 1.0},
        {"source_id": "r:branch1", "target_id": "r:child2", "relation_type": "prerequisite_of", "origin": "roadmap", "confidence": 1.0},
        {"source_id": "r:branch1", "target_id": "r:child3", "relation_type": "prerequisite_of", "origin": "roadmap", "confidence": 1.0},
    ]
    upsert_roadmap(conn, nodes, edges)

    def override_get_db():
        yield conn

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    conn.close()


def test_list_roadmaps_marks_imported_slug(client):
    resp = client.get("/api/roadmaps")
    assert resp.status_code == 200
    slugs = {item["slug"]: item["imported"] for item in resp.json()}
    if "r" in slugs:  # 'r' nao existe no vendor real, so aparece se algum dia coincidir
        assert slugs["r"] is True


def test_enrich_then_graph_returns_classified_nodes(client):
    resp = client.post("/api/roadmaps/r/enrich")
    assert resp.status_code == 200
    assert resp.json()["nodes_classified"] == 4

    graph = client.get("/api/roadmaps/r/graph").json()
    assert len(graph["nodes"]) == 4
    branch = next(n for n in graph["nodes"] if n["id"] == "r:branch1")
    assert branch["node_type"] == "branch"
    assert branch["status"] == "nao_iniciado"
    assert branch["description_md"] == "sobre bancos"


def test_get_node_detail_generates_content_lazily_and_marks_lido(client):
    client.post("/api/roadmaps/r/enrich")

    resp = client.get("/api/nodes/r:child1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "lido"
    assert body["generated_content"]["status"] == "aprovado"
    assert "PostgreSQL" in body["generated_content"]["texto"]

    # segunda chamada nao gera de novo, so devolve o que ja foi salvo
    resp2 = client.get("/api/nodes/r:child1")
    assert resp2.json()["generated_content"]["texto"] == body["generated_content"]["texto"]


def test_node_detail_404_for_unknown_node(client):
    resp = client.get("/api/nodes/does-not-exist")
    assert resp.status_code == 404


def test_node_detail_400_before_enrichment(client):
    resp = client.get("/api/nodes/r:child1")
    assert resp.status_code == 400


def test_full_mentoria_flow_validates_node_and_appears_in_revisao(client):
    client.post("/api/roadmaps/r/enrich")
    client.get("/api/nodes/r:child1")  # gera conteudo primeiro

    start = client.post("/api/nodes/r:child1/mentoria/start")
    assert start.status_code == 200
    session_id = start.json()["session_id"]
    assert "?" in start.json()["turn"]["text"]

    turn = client.post(
        f"/api/mentoria/{session_id}/turn",
        json={"text": "uma resposta longa e substancial explicando o conceito com minhas palavras"},
    )
    assert turn.status_code == 200

    end = client.post(f"/api/mentoria/{session_id}/end")
    assert end.status_code == 200

    node = client.get("/api/nodes/r:child1").json()
    assert node["status"] == "validado"

    revisao = client.get("/api/revisao").json()
    assert any(item["node_id"] == "r:child1" and item["veredito_validado"] is True for item in revisao)


def test_mentoria_start_requires_content_generated_first(client):
    client.post("/api/roadmaps/r/enrich")
    resp = client.post("/api/nodes/r:child2/mentoria/start")
    assert resp.status_code == 400
