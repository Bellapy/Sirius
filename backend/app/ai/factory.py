from app.ai.base import AIProvider
from app.ai.simulated import SimulatedAIProvider
from app.config import AI_MODE, ANTHROPIC_API_KEY


def get_provider() -> AIProvider:
    if AI_MODE == "simulated":
        return SimulatedAIProvider()

    if AI_MODE == "real":
        if not ANTHROPIC_API_KEY:
            raise RuntimeError(
                "AI_MODE=real requer ANTHROPIC_API_KEY definida no ambiente. "
                "Ver Fase 7 do plano — habilitar IA real exige aprovacao explicita "
                "e comeca por um unico no de teste."
            )
        from app.ai.anthropic_provider import AnthropicAIProvider

        return AnthropicAIProvider(api_key=ANTHROPIC_API_KEY)

    raise ValueError(f"AI_MODE desconhecido: {AI_MODE!r} (esperado 'simulated' ou 'real')")
