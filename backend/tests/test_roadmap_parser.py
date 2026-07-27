import sqlite3

import pytest

from app.config import ROADMAPS_DIR
from app.db import SCHEMA, upsert_roadmap
from app.roadmap_parser import list_available_roadmaps, parse_roadmap

pytestmark = pytest.mark.skipif(
    not ROADMAPS_DIR.exists(),
    reason="vendor/developer-roadmap nao foi clonado neste ambiente",
)


def test_list_available_roadmaps_includes_backend():
    assert "backend" in list_available_roadmaps()


def test_parse_roadmap_backend_has_real_nodes_and_edges():
    parsed = parse_roadmap("backend")

    assert len(parsed["nodes"]) > 0
    assert len(parsed["edges"]) > 0

    for node in parsed["nodes"]:
        assert node["id"].startswith("backend:")
        assert node["label"]
        assert node["roadmap_origin"] == "backend"

    node_ids = {n["id"] for n in parsed["nodes"]}
    for edge in parsed["edges"]:
        assert edge["source_id"] in node_ids
        assert edge["target_id"] in node_ids
        assert edge["relation_type"] == "prerequisite_of"
        assert edge["origin"] == "roadmap"


def test_parse_roadmap_filters_out_layout_nodes():
    parsed = parse_roadmap("backend")
    labels = [n["label"] for n in parsed["nodes"]]
    assert "" not in labels


def test_upsert_roadmap_is_idempotent():
    parsed = parse_roadmap("backend")
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)

    upsert_roadmap(conn, parsed["nodes"], parsed["edges"])
    upsert_roadmap(conn, parsed["nodes"], parsed["edges"])

    node_count = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
    edge_count = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]

    assert node_count == len(parsed["nodes"])
    assert edge_count == len(parsed["edges"])
