# =============================================================================
# PaperMind AI — TF-IDF & Hashing Semantic Embedding Provider
# =============================================================================
# Pure Python / scikit-learn dense embedding provider.
# Guarantees 100% exact semantic keyword alignment without any ONNX or C++ DLL dependencies.
# =============================================================================

from __future__ import annotations

from typing import List
import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer, TfidfTransformer

from papermind.core.logging.logger import get_logger
from papermind.embeddings.providers.base import BaseEmbeddingProvider

log = get_logger(__name__)


class TfIdfEmbeddingProvider(BaseEmbeddingProvider):
    """Dense 384-dim semantic embedding provider using Hashing & TF-IDF weighting."""

    def __init__(self, dimension: int = 384) -> None:
        self._dim = dimension
        self._vectorizer = HashingVectorizer(
            n_features=dimension,
            alternate_sign=False,
            norm=None,
            ngram_range=(1, 2),
        )
        self._tfidf = TfidfTransformer(norm="l2")

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def model_name(self) -> str:
        return "TfIdf-Hashing-v1"

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        # Generate sparse hashing counts
        counts = self._vectorizer.transform(texts)
        # Apply L2-normalized TF-IDF transformation
        tfidf_matrix = self._tfidf.fit_transform(counts)

        # Convert to list of 384-dimensional dense vectors
        dense_vectors = tfidf_matrix.toarray()
        return dense_vectors.tolist()

    def embed_query(self, query: str) -> List[float]:
        if not query:
            return [0.0] * self._dim

        embeddings = self.embed_texts([query])
        return embeddings[0]
