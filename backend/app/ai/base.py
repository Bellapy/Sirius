from abc import ABC, abstractmethod
from typing import Optional

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


class AIProvider(ABC):
    """Interface abstrata de acesso a IA. Ver skill node-classification-branching
    para as regras de classificacao, content-templates para geracao e
    audit-checklist para auditoria — esta classe so define o contrato.
    """

    @abstractmethod
    def classify_node_types(self, items: list[NodeClassificationInput]) -> list[NodeType]:
        """Confirma ou corrige o sinal estrutural de cada item. Uma entrada por no,
        chamado em lote (Batch API na implementacao real)."""

    @abstractmethod
    def classify_edges(
        self, items: list[EdgeClassificationInput]
    ) -> list[Optional[EdgeClassificationResult]]:
        """Classifica a relacao de cada par candidato. None = sem relacao real.
        Chamado em lote (Batch API na implementacao real)."""

    @abstractmethod
    def generate_content(self, item: ContentGenerationInput) -> str:
        """Gera o texto de um unico no, usando o template do seu node_type.
        Uma chamada isolada por no — nunca lote (ver skill content-templates)."""

    @abstractmethod
    def audit_content(self, text: str, edges: list[EdgeContext]) -> AuditResult:
        """Checagem mecanica pos-geracao (ver skill audit-checklist)."""

    @abstractmethod
    def mentoria_reply(
        self, node_content: str, history: list[MentoriaTurn], user_message: str
    ) -> str:
        """Proxima fala da mentora socratica, dado o conteudo do no e o historico
        da sessao atual."""
