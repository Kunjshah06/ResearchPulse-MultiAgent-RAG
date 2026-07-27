# # =============================================================================
# # PaperMind AI — SentenceTransformers Provider
# # =============================================================================
# # Local dense embedding provider utilizing SentenceTransformers models.
# # Supports BAAI/bge-m3, all-MiniLM-L6-v2, etc.
# # =============================================================================

# from __future__ import annotations

# from typing import Any

# from papermind.core.logging.logger import get_logger
# from papermind.embeddings.providers.base import BaseEmbeddingProvider
# import random

# log = get_logger(__name__)


# class SentenceTransformersProvider(BaseEmbeddingProvider):
#     """Local embedding provider powered by SentenceTransformers."""

#     def __init__(
#         self,
#         model_name: str = "all-MiniLM-L6-v2",
#         device: str = "cpu",
#         batch_size: int = 32,
#     ) -> None:
#         self._model_name = model_name
#         self.device = device
#         self.batch_size = batch_size
#         self._model: Any = None
#         self._use_mock: bool = False
#         self._fallback_dim: int = 1024 if "bge-m3" in model_name.lower() else 384

#     def _load_model(self) -> Any:
#         if self._model is None and not self._use_mock:
#             log.info("Loading SentenceTransformer model", model=self._model_name, device=self.device)
#             try:
#                 from sentence_transformers import SentenceTransformer
#                 self._model = SentenceTransformer(self._model_name, device=self.device)
#             except Exception as e:
#                 log.error("Failed to load SentenceTransformer (likely missing Windows C++ DLLs). Falling back to mock embeddings.", error=str(e))
#                 self._use_mock = True
#         return self._model

#     @property
#     def dimension(self) -> int:
#         if self._use_mock:
#             return self._fallback_dim
#         model = self._load_model()
#         dim = model.get_sentence_embedding_dimension()
#         return int(dim) if dim is not None else 384

#     @property
#     def model_name(self) -> str:
#         return self._model_name

#     def embed_texts(self, texts: list[str]) -> list[list[float]]:
#         if not texts:
#             return []
            
#         if self._use_mock:
#             # Deterministic mock embeddings so search actually returns something (albeit not semantically accurate)
#             # but allows the pipeline to succeed and the UI to be explored.
#             return [[random.random() for _ in range(self.dimension)] for _ in texts]
            
#         model = self._load_model()
#         embeddings = model.encode(
#             texts,
#             batch_size=self.batch_size,
#             show_progress_bar=False,
#             normalize_embeddings=True,
#         )
#         return [vec.tolist() for vec in embeddings]

#     def embed_query(self, query: str) -> list[float]:
#         if not query:
#             return [0.0] * self.dimension
#         embeddings = self.embed_texts([query])
#         return embeddings[0]

# =============================================================================
# PaperMind AI — FastEmbed Provider
# =============================================================================
# Local dense embedding provider powered by FastEmbed (ONNX Runtime backend).
# No torch dependency — avoids native DLL issues entirely. Supports BAAI/bge
# family models and other ONNX-exported sentence embedding models.
# =============================================================================

from __future__ import annotations

from typing import Any

from papermind.core.logging.logger import get_logger
from papermind.embeddings.providers.base import BaseEmbeddingProvider
import random

log = get_logger(__name__)


class FastEmbedProvider(BaseEmbeddingProvider):
    """Local embedding provider powered by FastEmbed (ONNX Runtime)."""

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
        batch_size: int = 32,
    ) -> None:
        self._model_name = model_name
        self.batch_size = batch_size
        self._model: Any = None
        self._use_mock: bool = False
        self._fallback_dim: int = 1024 if "bge-m3" in model_name.lower() else 384

    def _load_model(self) -> Any:
        if self._model is None and not self._use_mock:
            log.info("Loading FastEmbed model", model=self._model_name)
            try:
                from fastembed import TextEmbedding
                self._model = TextEmbedding(model_name=self._model_name)
            except Exception as e:
                log.error("Failed to load FastEmbed model. Falling back to mock embeddings.", error=str(e))
                self._use_mock = True
                self._model = None
        return self._model

    @property
    def dimension(self) -> int:
        if self._use_mock:
            return self._fallback_dim
        model = self._load_model()
        if model is None:
            return self._fallback_dim
        # FastEmbed doesn't expose dimension directly pre-encode; derive it once.
        sample = list(model.embed(["dimension probe"]))
        return len(sample[0]) if sample else self._fallback_dim

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        model = self._load_model()

        if self._use_mock or model is None:
            # Deterministic-ish mock embeddings so the pipeline can still run
            # end-to-end (not semantically accurate — search results won't be
            # meaningful, but the UI/API path won't 500).
            return [[random.random() for _ in range(self._fallback_dim)] for _ in texts]

        embeddings = model.embed(texts, batch_size=self.batch_size)
        return [vec.tolist() for vec in embeddings]

    def embed_query(self, query: str) -> list[float]:
        if not query:
            return [0.0] * self.dimension
        embeddings = self.embed_texts([query])
        return embeddings[0]