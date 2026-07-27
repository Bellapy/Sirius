"""Geracao de conteudo + auditoria de um unico no — ver skills
content-templates e audit-checklist para as regras. Nunca gerar em lote:
uma chamada isolada por no."""

from dataclasses import dataclass, field

from app.ai.base import AIProvider
from app.ai.types import ContentGenerationInput, EdgeContext

MAX_GENERATION_ATTEMPTS = 2


@dataclass
class AuditAttempt:
    tentativa: int
    aprovado: bool
    motivo: str | None


@dataclass
class GenerationResult:
    template_usado: str
    texto: str
    auditoria: list[AuditAttempt] = field(default_factory=list)
    status: str = "aprovado"  # "aprovado" | "revisar_manualmente"


def build_edge_context(node_id: str, edges: list[dict], node_by_id: dict[str, dict]) -> list[EdgeContext]:
    context = []
    for e in edges:
        if e["source_id"] == node_id:
            neighbor_id = e["target_id"]
        elif e["target_id"] == node_id:
            neighbor_id = e["source_id"]
        else:
            continue
        neighbor = node_by_id.get(neighbor_id)
        if neighbor is None:
            continue
        context.append(EdgeContext(
            neighbor_label=neighbor["label"],
            relation_type=e["relation_type"],
            confidence=e["confidence"],
        ))
    return context


def generate_and_audit(
    label: str,
    node_type: str,
    description_md: str | None,
    edge_context: list[EdgeContext],
    ai_provider: AIProvider,
) -> GenerationResult:
    auditoria: list[AuditAttempt] = []
    retry_reason: str | None = None
    texto = ""

    for attempt in range(1, MAX_GENERATION_ATTEMPTS + 1):
        content_input = ContentGenerationInput(
            label=label,
            node_type=node_type,
            description_md=description_md,
            edges=edge_context,
            retry_reason=retry_reason,
        )
        texto = ai_provider.generate_content(content_input)
        audit = ai_provider.audit_content(texto, edge_context)
        auditoria.append(AuditAttempt(tentativa=attempt, aprovado=audit.approved, motivo=audit.reason))

        if audit.approved:
            return GenerationResult(template_usado=node_type, texto=texto, auditoria=auditoria, status="aprovado")

        retry_reason = audit.reason

    return GenerationResult(
        template_usado=node_type, texto=texto, auditoria=auditoria, status="revisar_manualmente"
    )
