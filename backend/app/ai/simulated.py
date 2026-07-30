import re
from typing import Optional

from app.ai.base import AIProvider
from app.ai.types import (
    AuditResult,
    ContentGenerationInput,
    EdgeClassificationInput,
    EdgeClassificationResult,
    EdgeContext,
    MentoriaTurn,
    NodeClassificationInput,
    NodeType,
)

_TEMPLATE_SECTIONS = {
    "atomic_comparable": [
        "O que é", "Por que existe", "Casos de uso reais", "Trade-offs",
        "Comparação com alternativas", "Conexão com o resto do sistema", "Adoção de mercado",
    ],
    "atomic_conceptual": [
        "O que é", "Que problema resolve", "Onde falha na prática",
        "Conexão com outros nós", "Exemplo concreto",
    ],
    "branch": [
        "O que é", "Panorama do ecossistema", "Mapa de decisão", "Filhos",
    ],
}


class SimulatedAIProvider(AIProvider):
    """Sem custo, sem rede. Fixtures deterministicas para desenvolver e testar
    o resto do sistema antes de qualquer chamada real (ver CLAUDE.md,
    restricao de custo)."""

    def classify_node_types(self, items: list[NodeClassificationInput]) -> list[NodeType]:
        return [item.structural_guess for item in items]

    def classify_edges(
        self, items: list[EdgeClassificationInput]
    ) -> list[Optional[EdgeClassificationResult]]:
        results = []
        for item in items:
            if item.node_a_label.strip().lower() == item.node_b_label.strip().lower():
                results.append(None)
                continue
            results.append(EdgeClassificationResult(relation_type="prerequisite_of", confidence=0.75))
        return results

    def generate_content(self, item: ContentGenerationInput) -> str:
        sections = _TEMPLATE_SECTIONS[item.node_type]
        body = "\n\n".join(f"## {s}\n[simulado] conteúdo de '{s}' para {item.label}." for s in sections)
        if item.edges:
            neighbors = ", ".join(e.neighbor_label for e in item.edges)
            body += f"\n\nEssa nota conecta-se com {neighbors}."
        if item.retry_reason:
            body += f"\n\n[regenerado após reprovação: {item.retry_reason}]"
        return f"# {item.label}\n\n{body}"

    def audit_content(self, text: str, edges: list[EdgeContext]) -> AuditResult:
        if len(text.strip()) < 40:
            return AuditResult(False, "conteúdo curto demais / possível enchimento vazio")

        allowed = {e.neighbor_label.strip().lower() for e in edges}
        for match in re.findall(r"conecta-se com ([^.\n]+)", text):
            for candidate in match.split(","):
                candidate = candidate.strip().lower()
                if candidate and candidate not in allowed:
                    return AuditResult(
                        False, f"conexão '{candidate}' mencionada não está na lista de arestas fornecida"
                    )
        return AuditResult(True, None)

    def mentoria_reply(
        self, node_content: str, history: list[MentoriaTurn], user_message: str
    ) -> str:
        if not history:
            return "Antes de eu confirmar: como você explicaria isso pra alguém que nunca ouviu falar do assunto, sem usar os termos técnicos do texto?"
        return f"[simulado] Interessante — o que aconteceria se essa premissa que você descreveu ('{user_message[:40]}...') falhasse na prática?"

    def mentoria_veredito(self, node_content: str, history: list[MentoriaTurn]) -> tuple[bool, str]:
        respostas_substanciais = [
            t for t in history if t.role == "usuario" and len(t.text.strip()) > 15
        ]
        if respostas_substanciais:
            return True, "[simulado] Respostas demonstraram entendimento real, não só decoreba."
        return False, "[simulado] Sessão curta demais ou respostas rasas para validar."
