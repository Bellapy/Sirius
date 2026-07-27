import pytest

from app.ai.factory import get_provider
from app.ai.simulated import SimulatedAIProvider
from app.ai.types import (
    ContentGenerationInput,
    EdgeClassificationInput,
    EdgeContext,
    MentoriaTurn,
    NodeClassificationInput,
)


@pytest.fixture
def provider():
    return SimulatedAIProvider()


def test_get_provider_defaults_to_simulated(monkeypatch):
    monkeypatch.setattr("app.ai.factory.AI_MODE", "simulated")
    assert isinstance(get_provider(), SimulatedAIProvider)


def test_get_provider_real_without_key_raises(monkeypatch):
    monkeypatch.setattr("app.ai.factory.AI_MODE", "real")
    monkeypatch.setattr("app.ai.factory.ANTHROPIC_API_KEY", None)
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        get_provider()


def test_get_provider_unknown_mode_raises(monkeypatch):
    monkeypatch.setattr("app.ai.factory.AI_MODE", "bogus")
    with pytest.raises(ValueError):
        get_provider()


def test_classify_node_types_echoes_structural_guess(provider):
    items = [
        NodeClassificationInput(
            node_id="n1", label="PostgreSQL", description_md=None,
            neighbor_labels=["MySQL"], structural_guess="atomic_comparable",
        ),
        NodeClassificationInput(
            node_id="n2", label="Idempotencia", description_md=None,
            neighbor_labels=[], structural_guess="atomic_conceptual",
        ),
    ]
    assert provider.classify_node_types(items) == ["atomic_comparable", "atomic_conceptual"]


def test_classify_edges_same_label_returns_none(provider):
    items = [
        EdgeClassificationInput(
            pair_id="p1", node_a_label="Docker", node_a_description_md=None,
            node_b_label="Docker", node_b_description_md=None,
        ),
        EdgeClassificationInput(
            pair_id="p2", node_a_label="Docker", node_a_description_md=None,
            node_b_label="Kubernetes", node_b_description_md=None,
        ),
    ]
    results = provider.classify_edges(items)
    assert results[0] is None
    assert results[1].relation_type == "prerequisite_of"
    assert 0 < results[1].confidence <= 1


def test_generate_content_only_mentions_provided_edges(provider):
    edges = [EdgeContext(neighbor_label="MySQL", relation_type="alternative_to", confidence=0.9)]
    item = ContentGenerationInput(
        label="PostgreSQL", node_type="atomic_comparable", description_md=None, edges=edges,
    )
    text = provider.generate_content(item)
    assert "PostgreSQL" in text
    assert "MySQL" in text
    audit = provider.audit_content(text, edges)
    assert audit.approved


def test_audit_content_rejects_hallucinated_connection(provider):
    edges = [EdgeContext(neighbor_label="MySQL", relation_type="alternative_to", confidence=0.9)]
    hallucinated_text = "# Postgres\n\n" + ("x" * 40) + "\n\nEssa nota conecta-se com MongoDB."
    audit = provider.audit_content(hallucinated_text, edges)
    assert not audit.approved
    assert "mongodb" in audit.reason.lower()


def test_audit_content_rejects_short_filler_text(provider):
    audit = provider.audit_content("muito curto", [])
    assert not audit.approved


def test_mentoria_reply_first_turn_asks_question_not_answer(provider):
    reply = provider.mentoria_reply("conteudo do no", history=[], user_message="")
    assert "?" in reply


def test_mentoria_reply_followup_uses_history(provider):
    history = [MentoriaTurn(role="mentora", text="pergunta inicial?")]
    reply = provider.mentoria_reply("conteudo do no", history=history, user_message="minha resposta")
    assert "?" in reply


def test_mentoria_veredito_false_without_substantial_user_answers(provider):
    history = [MentoriaTurn(role="mentora", text="pergunta inicial?")]
    validado, motivo = provider.mentoria_veredito("conteudo do no", history)
    assert validado is False
    assert motivo


def test_mentoria_veredito_true_with_substantial_user_answer(provider):
    history = [
        MentoriaTurn(role="mentora", text="pergunta inicial?"),
        MentoriaTurn(role="usuario", text="uma resposta bem mais elaborada e substancial sobre o tema"),
    ]
    validado, motivo = provider.mentoria_veredito("conteudo do no", history)
    assert validado is True
    assert motivo
