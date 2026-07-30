"""Parsing das respostas de classificacao, compartilhado pelos providers
reais (Anthropic/Google/Groq). Modelos menores/mais fracos (ex: Groq
llama-3.1-8b) as vezes nao respeitam o vocabulario fechado pedido no
prompt — nunca confiar cegamente no texto devolvido, sempre validar
contra a lista fechada antes de deixar entrar no banco (que tem CHECK
constraint pra isso, mas falhar la quebra a chamada inteira em vez de
so descartar o par ruim)."""

import json
from typing import Optional

from app.ai.types import (
    VALID_NODE_TYPES,
    VALID_RELATION_TYPES,
    EdgeClassificationResult,
    NodeType,
)


def parse_node_type(raw: Optional[str], fallback: NodeType) -> NodeType:
    if raw is None:
        return fallback
    cleaned = raw.strip().lower()
    if cleaned in VALID_NODE_TYPES:
        return cleaned  # type: ignore[return-value]
    return fallback


def parse_edge_classification(raw: Optional[str]) -> Optional[EdgeClassificationResult]:
    """None = sem relacao real OU resposta invalida/fora do vocabulario
    fechado — em ambos os casos, o par simplesmente nao vira aresta."""
    if raw is None:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    relation_type = data.get("relation_type")
    if relation_type not in VALID_RELATION_TYPES:
        return None
    try:
        confidence = float(data.get("confidence", 0.5))
    except (TypeError, ValueError):
        confidence = 0.5
    return EdgeClassificationResult(relation_type=relation_type, confidence=confidence)
