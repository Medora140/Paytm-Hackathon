import hashlib
import math
from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)

EMBEDDING_DIMENSION = 384


class ChunkEmbedder:
    """
    Computes vector embeddings for document chunks.
    Matches schema embedding vector(384).
    Uses ChromaDB DefaultEmbeddingFunction (all-MiniLM-L6-v2 via ONNX) with resilient fallback.
    """

    def __init__(self, batch_size: int = 32):
        self.batch_size = batch_size
        self._embed_fn = None
        self._init_embedding_function()

    def _init_embedding_function(self):
        try:
            from chromadb.utils import embedding_functions
            self._embed_fn = embedding_functions.DefaultEmbeddingFunction()
        except Exception as e:
            logger.warning("Could not initialize ChromaDB embedding function: %s", e)
            self._embed_fn = None

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Embeds a list of strings into 384-dimensional float vectors.
        """
        if not texts:
            return []

        all_embeddings: List[List[float]] = []

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            batch_embeddings = []

            if self._embed_fn is not None:
                try:
                    raw_res = self._embed_fn(batch)
                    for item in raw_res:
                        vec = [float(x) for x in item]
                        # Ensure dimension matches 384
                        if len(vec) == EMBEDDING_DIMENSION:
                            batch_embeddings.append(vec)
                        elif len(vec) > EMBEDDING_DIMENSION:
                            batch_embeddings.append(vec[:EMBEDDING_DIMENSION])
                        else:
                            batch_embeddings.append(vec + [0.0] * (EMBEDDING_DIMENSION - len(vec)))
                except Exception as e:
                    logger.warning("Embedding function call failed for batch: %s. Using fallback vector generator.", e)
                    batch_embeddings = [self._fallback_embedding(t) for t in batch]
            else:
                batch_embeddings = [self._fallback_embedding(t) for t in batch]

            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    def embed_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Adds 384-dimensional 'embedding' key to each chunk dictionary.
        """
        texts = [c.get("text", "") for c in chunks]
        embeddings = self.embed_texts(texts)

        for chunk, emb in zip(chunks, embeddings):
            chunk["embedding"] = emb

        return chunks

    def _fallback_embedding(self, text: str) -> List[float]:
        """
        Deterministic pseudo-embedding generating normalized 384-dim vector
        used as fallback if external model runtime is unavailable.
        """
        vec = []
        # Use multiple hash seeds to project onto 384 dimensions
        for i in range(EMBEDDING_DIMENSION):
            h = hashlib.sha256(f"{text}_{i}".encode("utf-8")).digest()
            val = (int.from_bytes(h[:4], "big") / (2**32 - 1)) * 2.0 - 1.0
            vec.append(val)

        # Normalize to unit length
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [round(x / norm, 6) for x in vec]
