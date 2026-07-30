"""Provider real alternativo usando Groq (tier gratuito, sem cartao de
credito exigido, historicamente). Assim como o GoogleAIProvider, nao faz
parte do roteamento oficial do CLAUDE.md (Anthropic) — existe so pra testar
qualidade de geracao real sem custo, antes da Fase 7. Reusa os mesmos
prompts de sistema do AnthropicAIProvider."""

import json
import time
from typing import Optional

from groq import Groq

from app.ai.anthropic_provider import (
    AUDIT_SYSTEM,
    CLASSIFY_EDGE_SYSTEM,
    CLASSIFY_NODE_SYSTEM,
    GENERATE_CONTENT_SYSTEM,
    MENTORA_SYSTEM,
    VEREDITO_SYSTEM,
)
from app.ai.base import AIProvider
from app.ai.parsing import parse_edge_classification, parse_node_type
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

GROQ_MODELS = {
    "classify": "llama-3.1-8b-instant",
    "generate": "llama-3.3-70b-versatile",
    "audit": "llama-3.1-8b-instant",
    "mentoria": "llama-3.3-70b-versatile",
}

# Tier gratuito do Groq e bem mais folgado que o do Gemini, mas ainda vale
# espacar chamadas sequenciais de classificacao (sem Batch API gratuita aqui).
RATE_LIMIT_DELAY_SECONDS = 2


class GroqAIProvider(AIProvider):
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)

    def _generate(self, model: str, system: str, prompt: str, max_tokens: int) -> str:
        response = self.client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return (response.choices[0].message.content or "").strip()

    def classify_node_types(self, items: list[NodeClassificationInput]) -> list[NodeType]:
        results = []
        for item in items:
            prompt = (
                f"Palpite estrutural: {item.structural_guess}\n"
                f"No: {item.label}\nDescricao: {item.description_md or '(sem descricao)'}\n"
                f"Vizinhos: {', '.join(item.neighbor_labels) or '(nenhum)'}"
            )
            raw = self._generate(GROQ_MODELS["classify"], CLASSIFY_NODE_SYSTEM, prompt, 16)
            results.append(parse_node_type(raw, item.structural_guess))
            time.sleep(RATE_LIMIT_DELAY_SECONDS)
        return results

    def classify_edges(
        self, items: list[EdgeClassificationInput]
    ) -> list[Optional[EdgeClassificationResult]]:
        results = []
        for item in items:
            prompt = (
                f"No A: {item.node_a_label}\n{item.node_a_description_md or ''}\n\n"
                f"No B: {item.node_b_label}\n{item.node_b_description_md or ''}"
            )
            raw = self._generate(GROQ_MODELS["classify"], CLASSIFY_EDGE_SYSTEM, prompt, 64)
            results.append(parse_edge_classification(raw))
            time.sleep(RATE_LIMIT_DELAY_SECONDS)
        return results

    def generate_content(self, item: ContentGenerationInput) -> str:
        edges_json = json.dumps([
            {"neighbor_label": e.neighbor_label, "relation_type": e.relation_type, "confidence": e.confidence}
            for e in item.edges
        ], ensure_ascii=False)
        prompt = (
            f"node_type: {item.node_type}\nlabel: {item.label}\n"
            f"descricao original: {item.description_md or '(nenhuma)'}\n"
            f"arestas reais (unica fonte permitida de conexoes): {edges_json}"
        )
        if item.retry_reason:
            prompt += f"\n\nTentativa anterior reprovada. Motivo: {item.retry_reason}"
        return self._generate(GROQ_MODELS["generate"], GENERATE_CONTENT_SYSTEM, prompt, 2048)

    def audit_content(self, text: str, edges: list[EdgeContext]) -> AuditResult:
        edges_json = json.dumps([
            {"neighbor_label": e.neighbor_label, "relation_type": e.relation_type, "confidence": e.confidence}
            for e in edges
        ], ensure_ascii=False)
        raw = self._generate(
            GROQ_MODELS["audit"], AUDIT_SYSTEM,
            f"Texto:\n{text}\n\nArestas permitidas:\n{edges_json}", 128,
        )
        if raw.lower().startswith("aprovado"):
            return AuditResult(True, None)
        reason = raw.split(":", 1)[1].strip() if ":" in raw else raw
        return AuditResult(False, reason)

    def mentoria_reply(
        self, node_content: str, history: list[MentoriaTurn], user_message: str
    ) -> str:
        transcript = "\n".join(f"{t.role}: {t.text}" for t in history)
        prompt = f"Conteudo do no em avaliacao:\n{node_content}\n\n{transcript}\n\nusuario: {user_message}"
        return self._generate(GROQ_MODELS["mentoria"], MENTORA_SYSTEM, prompt, 512)

    def mentoria_veredito(self, node_content: str, history: list[MentoriaTurn]) -> tuple[bool, str]:
        transcript = "\n".join(f"{t.role}: {t.text}" for t in history)
        raw = self._generate(
            GROQ_MODELS["mentoria"], VEREDITO_SYSTEM,
            f"Conteudo do topico:\n{node_content}\n\nTranscricao da sessao:\n{transcript}", 128,
        )
        try:
            data = json.loads(raw)
            return bool(data["validado"]), str(data.get("motivo", ""))
        except (json.JSONDecodeError, KeyError):
            return False, "resposta da avaliacao em formato inesperado"

