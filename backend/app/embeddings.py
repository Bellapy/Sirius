import hashlib
from abc import ABC, abstractmethod

import numpy as np

from app.config import EMBEDDING_MODE, EMBEDDING_MODEL_NAME


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[np.ndarray]:
        """Retorna um vetor float32 por texto, na mesma ordem."""


class SimulatedEmbeddingProvider(EmbeddingProvider):
    """Hash determinístico, sem modelo, sem custo — so para dev/testes rapidos
    do pipeline. Nao tem semantica real, nao usar para decidir similaridade
    de conteudo de verdade."""

    dim = 64

    def embed(self, texts: list[str]) -> list[np.ndarray]:
        vectors = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            needed = self.dim * 4
            raw = (digest * (needed // len(digest) + 1))[:needed]
            vectors.append(np.frombuffer(raw, dtype=np.uint8).astype(np.float32))
        return vectors


class LocalSentenceTransformerEmbeddingProvider(EmbeddingProvider):
    """Modelo local (sentence-transformers) — zero custo de API, roda na
    maquina do usuario. Import de sentence_transformers e lazy para nao
    pagar o custo de carregar torch em quem so usa o modo simulado."""

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)

    def embed(self, texts: list[str]) -> list[np.ndarray]:
        vectors = self._model.encode(texts, normalize_embeddings=False)
        return [np.asarray(v, dtype=np.float32) for v in vectors]


def get_embedding_provider() -> EmbeddingProvider:
    if EMBEDDING_MODE == "simulated":
        return SimulatedEmbeddingProvider()
    if EMBEDDING_MODE == "local":
        return LocalSentenceTransformerEmbeddingProvider()
    raise ValueError(f"EMBEDDING_MODE desconhecido: {EMBEDDING_MODE!r} (esperado 'simulated' ou 'local')")
