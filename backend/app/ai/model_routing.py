"""Roteamento de modelo por tarefa — ver CLAUDE.md para a tabela e a
justificativa. Nunca Opus, nunca raciocinio estendido."""

TASK_MODELS = {
    "classify_node_types": "claude-haiku-4-5-20251001",
    "classify_edges": "claude-haiku-4-5-20251001",
    "generate_content": "claude-sonnet-5",
    "audit_content": "claude-haiku-4-5-20251001",
    "mentoria_reply": "claude-sonnet-5",
}
