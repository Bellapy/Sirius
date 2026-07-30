import pytest


@pytest.fixture(autouse=True)
def _never_use_real_ai_in_tests(monkeypatch):
    """Rede de seguranca: um .env local com AI_MODE=real/google (chave de
    verdade) nunca deve vazar pra suite de testes, mesmo que um teste novo
    esqueca de isolar isso explicitamente."""
    monkeypatch.setattr("app.ai.factory.AI_MODE", "simulated")
    monkeypatch.setattr("app.embeddings.EMBEDDING_MODE", "simulated")
