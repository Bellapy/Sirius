import sqlite3

from app.ai.base import AIProvider
from app.ai.simulated import SimulatedAIProvider
from app.ai.types import AuditResult, ContentGenerationInput, EdgeContext
from app.content_generation import MAX_GENERATION_ATTEMPTS, build_edge_context, generate_and_audit
from app.db import SCHEMA, save_enrichment_results, upsert_roadmap
from app.generate_node_content import generate_for_node


def test_build_edge_context_handles_both_directions():
    edges = [
        {"source_id": "a", "target_id": "b", "relation_type": "prerequisite_of", "origin": "roadmap", "confidence": 1.0},
        {"source_id": "c", "target_id": "a", "relation_type": "alternative_to", "origin": "roadmap", "confidence": 0.8},
        {"source_id": "x", "target_id": "y", "relation_type": "prerequisite_of", "origin": "roadmap", "confidence": 1.0},
    ]
    node_by_id = {"b": {"id": "b", "label": "B label"}, "c": {"id": "c", "label": "C label"}}
    context = build_edge_context("a", edges, node_by_id)
    labels = {c.neighbor_label for c in context}
    assert labels == {"B label", "C label"}


def test_generate_and_audit_approves_first_try_with_simulated_provider():
    edges = [EdgeContext(neighbor_label="MySQL", relation_type="alternative_to", confidence=0.9)]
    result = generate_and_audit(
        label="PostgreSQL", node_type="atomic_comparable", description_md=None,
        edge_context=edges, ai_provider=SimulatedAIProvider(),
    )
    assert result.status == "aprovado"
    assert len(result.auditoria) == 1
    assert result.auditoria[0].aprovado


class _AlwaysReproveProvider(AIProvider):
    def __init__(self):
        self.retry_reasons_seen = []

    def classify_node_types(self, items):
        raise NotImplementedError

    def classify_edges(self, items):
        raise NotImplementedError

    def generate_content(self, item: ContentGenerationInput) -> str:
        self.retry_reasons_seen.append(item.retry_reason)
        return "texto de enchimento"

    def audit_content(self, text, edges) -> AuditResult:
        return AuditResult(False, "sempre reprovado para teste")

    def mentoria_reply(self, node_content, history, user_message) -> str:
        raise NotImplementedError

    def mentoria_veredito(self, node_content, history):
        raise NotImplementedError


def test_generate_and_audit_marks_revisar_manualmente_after_max_attempts():
    provider = _AlwaysReproveProvider()
    result = generate_and_audit(
        label="No dificil", node_type="atomic_conceptual", description_md=None,
        edge_context=[], ai_provider=provider,
    )
    assert result.status == "revisar_manualmente"
    assert len(result.auditoria) == MAX_GENERATION_ATTEMPTS
    assert all(not a.aprovado for a in result.auditoria)
    # primeira tentativa sem motivo de retry, tentativas seguintes recebem o motivo da reprovacao anterior
    assert provider.retry_reasons_seen[0] is None
    assert provider.retry_reasons_seen[1] == "sempre reprovado para teste"


class _ApprovesOnSecondTryProvider(AIProvider):
    def classify_node_types(self, items):
        raise NotImplementedError

    def classify_edges(self, items):
        raise NotImplementedError

    def generate_content(self, item: ContentGenerationInput) -> str:
        if item.retry_reason:
            return "texto corrigido e valido " + "x" * 40
        return "primeiro texto ruim"

    def audit_content(self, text, edges) -> AuditResult:
        if "corrigido" in text:
            return AuditResult(True, None)
        return AuditResult(False, "motivo da primeira reprovacao")

    def mentoria_reply(self, node_content, history, user_message) -> str:
        raise NotImplementedError

    def mentoria_veredito(self, node_content, history):
        raise NotImplementedError


def test_generate_and_audit_recovers_on_retry():
    result = generate_and_audit(
        label="No", node_type="atomic_conceptual", description_md=None,
        edge_context=[], ai_provider=_ApprovesOnSecondTryProvider(),
    )
    assert result.status == "aprovado"
    assert len(result.auditoria) == 2
    assert result.auditoria[0].aprovado is False
    assert result.auditoria[1].aprovado is True


def test_generate_for_node_end_to_end_persists_generated_content():
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)

    nodes = [
        {"id": "a", "label": "PostgreSQL", "roadmap_origin": "r", "description_md": "banco relacional"},
        {"id": "b", "label": "MySQL", "roadmap_origin": "r", "description_md": "outro banco relacional"},
    ]
    edges = [{"source_id": "a", "target_id": "b", "relation_type": "alternative_to", "origin": "roadmap", "confidence": 0.9}]
    upsert_roadmap(conn, nodes, edges)
    save_enrichment_results(conn, {"a": "atomic_comparable", "b": "atomic_comparable"}, [], {})

    generated = generate_for_node(conn, "a", SimulatedAIProvider())

    assert generated["status"] == "aprovado"
    assert "MySQL" in generated["texto"]

    row = conn.execute("SELECT generated_content FROM nodes WHERE id = 'a'").fetchone()
    assert row[0] is not None
