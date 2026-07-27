import sqlite3

import networkx as nx
import pytest

from app.ai.simulated import SimulatedAIProvider
from app.db import SCHEMA, fetch_roadmap_graph, save_enrichment_results, upsert_roadmap
from app.embeddings import SimulatedEmbeddingProvider
from app.graph_pipeline import (
    BRANCH_CHILD_THRESHOLD,
    build_graph,
    compute_embeddings,
    enrich_graph,
    filter_candidate_pairs,
    structural_guess,
)


def make_node(id_, label, description_md=None, roadmap_origin="r"):
    return {"id": id_, "label": label, "roadmap_origin": roadmap_origin, "description_md": description_md}


def test_compute_embeddings_one_vector_per_node():
    nodes = [make_node("a", "Docker"), make_node("b", "Kubernetes")]
    embeddings = compute_embeddings(nodes, SimulatedEmbeddingProvider())
    assert set(embeddings.keys()) == {"a", "b"}
    assert embeddings["a"].shape == embeddings["b"].shape


def test_filter_candidate_pairs_skips_existing_edges():
    # texto identico -> embedding identico -> similaridade 1.0, sempre candidato
    nodes = [make_node("a", "X", "mesmo texto"), make_node("b", "X", "mesmo texto"), make_node("c", "Z", "outro totalmente diferente 12345")]
    embeddings = compute_embeddings(nodes, SimulatedEmbeddingProvider())
    node_ids = [n["id"] for n in nodes]

    pairs_no_existing = filter_candidate_pairs(node_ids, embeddings, [], threshold=0.99)
    assert ("a", "b") in pairs_no_existing

    existing = [{"source_id": "a", "target_id": "b", "relation_type": "prerequisite_of", "origin": "roadmap", "confidence": 1.0}]
    pairs_with_existing = filter_candidate_pairs(node_ids, embeddings, existing, threshold=0.99)
    assert ("a", "b") not in pairs_with_existing


def test_structural_guess_branch_when_many_children():
    graph = nx.DiGraph()
    graph.add_node("parent")
    for i in range(BRANCH_CHILD_THRESHOLD):
        child = f"child{i}"
        graph.add_node(child)
        graph.add_edge("parent", child, relation_type="prerequisite_of")
    assert structural_guess("parent", graph) == "branch"


def test_structural_guess_atomic_comparable_when_alternative_edge():
    graph = nx.DiGraph()
    graph.add_edge("postgres", "mysql", relation_type="alternative_to")
    assert structural_guess("postgres", graph) == "atomic_comparable"


def test_structural_guess_atomic_conceptual_default():
    graph = nx.DiGraph()
    graph.add_node("idempotencia")
    assert structural_guess("idempotencia", graph) == "atomic_conceptual"


def test_enrich_graph_end_to_end_with_simulated_providers():
    nodes = [
        make_node("branch1", "Bancos de Dados", "sobre bancos de dados relacionais e nao relacionais"),
        make_node("child1", "PostgreSQL", "banco relacional open source"),
        make_node("child2", "MongoDB", "banco nao relacional orientado a documentos"),
        make_node("child3", "Redis", "banco em memoria chave-valor"),
    ]
    edges = [
        {"source_id": "branch1", "target_id": "child1", "relation_type": "prerequisite_of", "origin": "roadmap", "confidence": 1.0},
        {"source_id": "branch1", "target_id": "child2", "relation_type": "prerequisite_of", "origin": "roadmap", "confidence": 1.0},
        {"source_id": "branch1", "target_id": "child3", "relation_type": "prerequisite_of", "origin": "roadmap", "confidence": 1.0},
    ]

    result = enrich_graph(nodes, edges, SimulatedAIProvider(), SimulatedEmbeddingProvider())

    assert result["node_types"]["branch1"] == "branch"
    assert set(result["embeddings"].keys()) == {"branch1", "child1", "child2", "child3"}
    assert all(nt in ("atomic_comparable", "atomic_conceptual", "branch") for nt in result["node_types"].values())


def test_save_enrichment_results_persists_node_type_embedding_and_edges():
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)

    nodes = [make_node("a", "PostgreSQL", "banco relacional", roadmap_origin="r"), make_node("b", "MySQL", "banco relacional", roadmap_origin="r")]
    upsert_roadmap(conn, nodes, [])

    fetched_nodes, fetched_edges = fetch_roadmap_graph(conn, "r")
    assert len(fetched_nodes) == 2
    assert fetched_edges == []

    result = enrich_graph(fetched_nodes, fetched_edges, SimulatedAIProvider(), SimulatedEmbeddingProvider())
    save_enrichment_results(conn, result["node_types"], result["new_edges"], result["embeddings"])

    row = conn.execute("SELECT node_type, embedding FROM nodes WHERE id = 'a'").fetchone()
    assert row[0] in ("atomic_comparable", "atomic_conceptual", "branch")
    assert row[1] is not None
