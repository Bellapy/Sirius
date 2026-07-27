"""Pipeline de enriquecimento do grafo — ver skill node-classification-branching
para as regras de classificacao. Orquestra: embeddings -> filtro de pares
candidatos por similaridade -> classificacao de arestas -> sinal estrutural
(networkx) + confirmacao semantica -> classificacao de tipo de no.
"""

import numpy as np
import networkx as nx

from app.ai.base import AIProvider
from app.ai.types import EdgeClassificationInput, NodeClassificationInput, NodeType
from app.embeddings import EmbeddingProvider

SIMILARITY_THRESHOLD = 0.6
BRANCH_CHILD_THRESHOLD = 3


def compute_embeddings(nodes: list[dict], provider: EmbeddingProvider) -> dict[str, np.ndarray]:
    texts = [f"{n['label']}\n\n{n['description_md'] or ''}" for n in nodes]
    vectors = provider.embed(texts)
    return {n["id"]: v for n, v in zip(nodes, vectors)}


def filter_candidate_pairs(
    node_ids: list[str],
    embeddings: dict[str, np.ndarray],
    existing_edges: list[dict],
    threshold: float = SIMILARITY_THRESHOLD,
) -> list[tuple[str, str]]:
    existing_pairs = set()
    for e in existing_edges:
        existing_pairs.add((e["source_id"], e["target_id"]))
        existing_pairs.add((e["target_id"], e["source_id"]))

    matrix = np.array([embeddings[i] for i in node_ids])
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1
    normalized = matrix / norms
    similarity = normalized @ normalized.T

    pairs = []
    n = len(node_ids)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = node_ids[i], node_ids[j]
            if (a, b) in existing_pairs:
                continue
            if similarity[i, j] >= threshold:
                pairs.append((a, b))
    return pairs


def build_graph(nodes: list[dict], edges: list[dict]) -> nx.DiGraph:
    graph = nx.DiGraph()
    for n in nodes:
        graph.add_node(n["id"])
    for e in edges:
        graph.add_edge(e["source_id"], e["target_id"], relation_type=e["relation_type"])
    return graph


def structural_guess(node_id: str, graph: nx.DiGraph) -> NodeType:
    """Sinal estrutural automatico, sem custo de IA — ver skill
    node-classification-branching."""
    has_alternative = any(
        data.get("relation_type") == "alternative_to"
        for _, _, data in list(graph.out_edges(node_id, data=True)) + list(graph.in_edges(node_id, data=True))
    )
    if has_alternative:
        return "atomic_comparable"
    if graph.out_degree(node_id) >= BRANCH_CHILD_THRESHOLD:
        return "branch"
    return "atomic_conceptual"


def enrich_graph(
    nodes: list[dict],
    edges: list[dict],
    ai_provider: AIProvider,
    embedding_provider: EmbeddingProvider,
) -> dict:
    """Roda o pipeline completo sobre um grafo ja importado (nodes/edges no
    formato do schema). Nao persiste — devolve os resultados para o chamador
    gravar no banco."""
    node_by_id = {n["id"]: n for n in nodes}
    node_ids = [n["id"] for n in nodes]

    embeddings = compute_embeddings(nodes, embedding_provider)

    candidate_pairs = filter_candidate_pairs(node_ids, embeddings, edges)
    edge_items = [
        EdgeClassificationInput(
            pair_id=f"{a}|{b}",
            node_a_label=node_by_id[a]["label"],
            node_a_description_md=node_by_id[a]["description_md"],
            node_b_label=node_by_id[b]["label"],
            node_b_description_md=node_by_id[b]["description_md"],
        )
        for a, b in candidate_pairs
    ]
    edge_results = ai_provider.classify_edges(edge_items) if edge_items else []

    new_edges = []
    for (a, b), result in zip(candidate_pairs, edge_results):
        if result is None:
            continue
        new_edges.append({
            "source_id": a,
            "target_id": b,
            "relation_type": result.relation_type,
            "origin": "llm_inferred",
            "confidence": result.confidence,
        })

    graph = build_graph(nodes, edges + new_edges)

    node_items = []
    for n in nodes:
        guess = structural_guess(n["id"], graph)
        neighbor_ids = set(graph.successors(n["id"])) | set(graph.predecessors(n["id"]))
        neighbor_labels = [node_by_id[nb]["label"] for nb in neighbor_ids if nb in node_by_id]
        node_items.append(NodeClassificationInput(
            node_id=n["id"],
            label=n["label"],
            description_md=n["description_md"],
            neighbor_labels=neighbor_labels,
            structural_guess=guess,
        ))
    confirmed_types = ai_provider.classify_node_types(node_items) if node_items else []
    node_types = dict(zip(node_ids, confirmed_types))

    return {"embeddings": embeddings, "new_edges": new_edges, "node_types": node_types}
