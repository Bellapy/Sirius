from app.ai.base import AIProvider
from app.ai.simulated import SimulatedAIProvider
from app.config import AI_MODE, ANTHROPIC_API_KEY, GOOGLE_API_KEY, GROQ_API_KEY


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

    if AI_MODE == "google":
        if not GOOGLE_API_KEY:
            raise RuntimeError(
                "AI_MODE=google requer GOOGLE_API_KEY definida no ambiente "
                "(chave gratuita gerada em aistudio.google.com/apikey). Provider "
                "de teste, fora do roteamento oficial (que e Anthropic) — so para "
                "validar qualidade de geracao real sem custo."
            )
        from app.ai.google_provider import GoogleAIProvider

        return GoogleAIProvider(api_key=GOOGLE_API_KEY)

    if AI_MODE == "groq":
        if not GROQ_API_KEY:
            raise RuntimeError(
                "AI_MODE=groq requer GROQ_API_KEY definida no ambiente "
                "(chave gratuita gerada em console.groq.com/keys). Provider de "
                "teste, fora do roteamento oficial (que e Anthropic) — so para "
                "validar qualidade de geracao real sem custo."
            )
        from app.ai.groq_provider import GroqAIProvider

        return GroqAIProvider(api_key=GROQ_API_KEY)

    raise ValueError(
        f"AI_MODE desconhecido: {AI_MODE!r} (esperado 'simulated', 'real', 'google' ou 'groq')"
    )
