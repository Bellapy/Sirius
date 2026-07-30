import json
import time
from typing import Optional

import anthropic

from app.ai.base import AIProvider
from app.ai.model_routing import TASK_MODELS
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

CLASSIFY_NODE_SYSTEM = (
    "Voce classifica nos de um grafo de estudo em exatamente um de tres tipos: "
    "atomic_comparable, atomic_conceptual, branch. Recebe um sinal estrutural "
    "(palpite automatico baseado em centralidade do grafo) e o no + vizinhos "
    "diretos. Confirme o palpite ou corrija. Responda so com o tipo, nada mais."
)

CLASSIFY_EDGE_SYSTEM = (
    "Voce classifica a relacao entre dois nos de um grafo de estudo, usando "
    "exclusivamente um destes 5 valores: prerequisite_of, alternative_to, "
    "contrasts_with, composes_with, applied_in. Se nao houver relacao real, "
    "responda 'none'. Responda em JSON: {\"relation_type\": ..., \"confidence\": ...} "
    "ou {\"relation_type\": \"none\"}."
)

GENERATE_CONTENT_SYSTEM = (
    "Voce escreve conteudo educacional denso e sem explicacao rasa para um no "
    "de um grafo de estudo, seguindo rigidamente a estrutura de secoes do "
    "template do node_type informado. Voce recebe a lista fechada de arestas "
    "reais desse no e SO PODE tecer conexoes dessa lista — nunca inventar uma "
    "conexao nova."
)

AUDIT_SYSTEM = (
    "Voce audita um texto ja gerado, sem te-lo escrito. Checa mecanicamente: "
    "(1) toda conexao mencionada no texto esta na lista de arestas fornecida? "
    "(2) o texto nao e conteudo de enchimento artificial? Responda so "
    "'aprovado' ou 'reprovado: <motivo curto>'."
)

MENTORA_SYSTEM = (
    "Voce e uma mentora socratica. Nunca responde com explicacao direta, "
    "sempre com perguntas direcionais. Proibido jargao obvio ao pedir que o "
    "usuario explique um conceito. Detecta resposta decorada. Propoe desafios "
    "praticos que combinem conceitos. Ajusta dificuldade dinamicamente. Fala "
    "menos que o usuario — sem monologos longos."
)

VEREDITO_SYSTEM = (
    "Voce e uma avaliadora tecnica senior, estilo entrevista de emprego. "
    "Dado o conteudo de um topico e a transcricao de uma sessao de mentoria "
    "socratica sobre ele, decida se o usuario demonstrou entendimento real "
    "(nao so memorizacao). Responda so em JSON: "
    "{\"validado\": true|false, \"motivo\": \"<frase curta>\"}."
)


def _cached_system(text: str) -> list[dict]:
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]


class AnthropicAIProvider(AIProvider):
    """Implementacao real. So deve ser instanciada com AI_MODE=real e uma
    ANTHROPIC_API_KEY valida — ver Fase 7 do plano (aprovacao explicita do
    usuario, comecando por um unico no de teste)."""

    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def classify_node_types(self, items: list[NodeClassificationInput]) -> list[NodeType]:
        if not items:
            return []
        requests = [
            anthropic.types.message_create_params.MessageCreateParamsNonStreaming(
                model=TASK_MODELS["classify_node_types"],
                max_tokens=16,
                system=_cached_system(CLASSIFY_NODE_SYSTEM),
                messages=[{
                    "role": "user",
                    "content": (
                        f"Palpite estrutural: {item.structural_guess}\n"
                        f"No: {item.label}\nDescricao: {item.description_md or '(sem descricao)'}\n"
                        f"Vizinhos: {', '.join(item.neighbor_labels) or '(nenhum)'}"
                    ),
                }],
            )
            for item in items
        ]
        batch_requests = [
            anthropic.types.messages.batch_create_params.Request(custom_id=item.node_id, params=req)
            for item, req in zip(items, requests)
        ]
        results_by_id = self._run_batch(batch_requests)
        return [parse_node_type(results_by_id.get(item.node_id), item.structural_guess) for item in items]

    def classify_edges(
        self, items: list[EdgeClassificationInput]
    ) -> list[Optional[EdgeClassificationResult]]:
        if not items:
            return []
        batch_requests = [
            anthropic.types.messages.batch_create_params.Request(
                custom_id=item.pair_id,
                params=anthropic.types.message_create_params.MessageCreateParamsNonStreaming(
                    model=TASK_MODELS["classify_edges"],
                    max_tokens=64,
                    system=_cached_system(CLASSIFY_EDGE_SYSTEM),
                    messages=[{
                        "role": "user",
                        "content": (
                            f"No A: {item.node_a_label}\n{item.node_a_description_md or ''}\n\n"
                            f"No B: {item.node_b_label}\n{item.node_b_description_md or ''}"
                        ),
                    }],
                ),
            )
            for item in items
        ]
        results_by_id = self._run_batch(batch_requests)
        return [parse_edge_classification(results_by_id.get(item.pair_id)) for item in items]

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
        response = self.client.messages.create(
            model=TASK_MODELS["generate_content"],
            max_tokens=2048,
            system=_cached_system(GENERATE_CONTENT_SYSTEM),
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def audit_content(self, text: str, edges: list[EdgeContext]) -> AuditResult:
        edges_json = json.dumps([
            {"neighbor_label": e.neighbor_label, "relation_type": e.relation_type, "confidence": e.confidence}
            for e in edges
        ], ensure_ascii=False)
        response = self.client.messages.create(
            model=TASK_MODELS["audit_content"],
            max_tokens=128,
            system=_cached_system(AUDIT_SYSTEM),
            messages=[{"role": "user", "content": f"Texto:\n{text}\n\nArestas permitidas:\n{edges_json}"}],
        )
        raw = response.content[0].text.strip()
        if raw.lower().startswith("aprovado"):
            return AuditResult(True, None)
        reason = raw.split(":", 1)[1].strip() if ":" in raw else raw
        return AuditResult(False, reason)

    def mentoria_reply(
        self, node_content: str, history: list[MentoriaTurn], user_message: str
    ) -> str:
        messages = [{
            "role": "user",
            "content": f"Conteudo do no em avaliacao:\n{node_content}",
        }]
        for turn in history:
            role = "assistant" if turn.role == "mentora" else "user"
            messages.append({"role": role, "content": turn.text})
        messages.append({"role": "user", "content": user_message})

        response = self.client.messages.create(
            model=TASK_MODELS["mentoria_reply"],
            max_tokens=512,
            system=_cached_system(MENTORA_SYSTEM),
            messages=messages,
        )
        return response.content[0].text

    def mentoria_veredito(self, node_content: str, history: list[MentoriaTurn]) -> tuple[bool, str]:
        transcript = "\n".join(f"{t.role}: {t.text}" for t in history)
        response = self.client.messages.create(
            model=TASK_MODELS["mentoria_reply"],
            max_tokens=128,
            system=_cached_system(VEREDITO_SYSTEM),
            messages=[{
                "role": "user",
                "content": f"Conteudo do topico:\n{node_content}\n\nTranscricao da sessao:\n{transcript}",
            }],
        )
        raw = response.content[0].text.strip()
        try:
            data = json.loads(raw)
            return bool(data["validado"]), str(data.get("motivo", ""))
        except (json.JSONDecodeError, KeyError):
            return False, "resposta da avaliacao em formato inesperado"

    def _run_batch(self, requests: list) -> dict[str, str]:
        batch = self.client.messages.batches.create(requests=requests)
        while True:
            status = self.client.messages.batches.retrieve(batch.id)
            if status.processing_status == "ended":
                break
            time.sleep(5)
        results: dict[str, str] = {}
        for entry in self.client.messages.batches.results(batch.id):
            if entry.result.type == "succeeded":
                results[entry.custom_id] = entry.result.message.content[0].text
        return results

