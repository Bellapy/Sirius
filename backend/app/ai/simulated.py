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
        "O que e", "Por que existe", "Casos de uso reais", "Trade-offs",
        "Comparacao com alternativas", "Conexao com o resto do sistema", "Adocao de mercado",
    ],
    "atomic_conceptual": [
        "O que e", "Que problema resolve", "Onde falha na pratica",
        "Conexao com outros nos", "Exemplo concreto",
    ],
    "branch": [
        "O que e", "Panorama do ecossistema", "Mapa de decisao", "Filhos",
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
        body = "\n\n".join(f"## {s}\n[simulado] conteudo de '{s}' para {item.label}." for s in sections)
        if item.edges:
            neighbors = ", ".join(e.neighbor_label for e in item.edges)
            body += f"\n\nEssa nota conecta-se com {neighbors}."
        if item.retry_reason:
            body += f"\n\n[regenerado apos reprovacao: {item.retry_reason}]"
        return f"# {item.label}\n\n{body}"

    def audit_content(self, text: str, edges: list[EdgeContext]) -> AuditResult:
        if len(text.strip()) < 40:
            return AuditResult(False, "conteudo curto demais / possivel enchimento vazio")

        allowed = {e.neighbor_label.strip().lower() for e in edges}
        for match in re.findall(r"conecta-se com ([^.\n]+)", text):
            for candidate in match.split(","):
                candidate = candidate.strip().lower()
                if candidate and candidate not in allowed:
                    return AuditResult(
                        False, f"conexao '{candidate}' mencionada nao esta na lista de arestas fornecida"
                    )
        return AuditResult(True, None)

    def mentoria_reply(
        self, node_content: str, history: list[MentoriaTurn], user_message: str
    ) -> str:
        if not history:
            return "Antes de eu confirmar: como voce explicaria isso pra alguem que nunca ouviu falar do assunto, sem usar os termos tecnicos do texto?"
        return f"[simulado] Interessante — o que aconteceria se essa premissa que voce descreveu ('{user_message[:40]}...') falhasse na pratica?"

    def mentoria_veredito(self, node_content: str, history: list[MentoriaTurn]) -> tuple[bool, str]:
        respostas_substanciais = [
            t for t in history if t.role == "usuario" and len(t.text.strip()) > 15
        ]
        if respostas_substanciais:
            return True, "[simulado] Respostas demonstraram entendimento real, nao so decoreba."
        return False, "[simulado] Sessao curta demais ou respostas rasas para validar."
