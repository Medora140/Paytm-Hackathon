import hashlib
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EXPECTED_EMBEDDING_DIMENSION = 384

# Global cached model instance to ensure model is loaded only once
_sentence_transformer_model = None


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9\u0900-\u097f]{2,}", (text or "").lower())


def _token_hash_vector(tokens: List[str], dimension: int = EXPECTED_EMBEDDING_DIMENSION) -> List[float]:
    vector = [0.0] * dimension
    if not tokens:
        return vector
    counts: Dict[int, float] = {}
    for token in tokens:
        idx = int(hashlib.sha1(token.encode("utf-8")).hexdigest(), 16) % dimension
        counts[idx] = counts.get(idx, 0.0) + 1.0
    norm = sum(v * v for v in counts.values()) ** 0.5
    if norm:
        for idx, val in counts.items():
            vector[idx] = val / norm
    return vector


def get_embedding_model():
    """
    Returns the singleton SentenceTransformer instance.
    Falls back to a deterministic keyword hash vector if the model is unavailable.
    """
    global _sentence_transformer_model
    if _sentence_transformer_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading local SentenceTransformer model '%s'...", EMBEDDING_MODEL_NAME)
            _sentence_transformer_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
            logger.info("SentenceTransformer model '%s' loaded successfully.", EMBEDDING_MODEL_NAME)
        except Exception as exc:
            logger.warning("SentenceTransformer not available; using deterministic fallback embeddings. Error: %s", exc)
            _sentence_transformer_model = "fallback"
    return _sentence_transformer_model


class ChunkEmbedder:
    """
    Computes real vector embeddings for document chunks using a local
    SentenceTransformer model (sentence-transformers/all-MiniLM-L6-v2).
    Generates exact 384-dimensional float vectors matching the
    PostgreSQL/pgvector schema: document_chunks.embedding vector(384).
    """

    def __init__(self, batch_size: int = 32):
        self.batch_size = batch_size

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Embeds a list of strings into 384-dimensional float vectors.
        Uses real SentenceTransformer embeddings when available; otherwise
        falls back to a deterministic hash-based vector to keep the pipeline working.
        """
        if not texts:
            return []

        model = get_embedding_model()
        if model == "fallback":
            return [_token_hash_vector(_tokenize(text)) for text in texts]

        all_embeddings: List[List[float]] = []

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            vectors = model.encode(batch, convert_to_numpy=True, normalize_embeddings=True)
            for vec in vectors:
                vec_list = [float(x) for x in vec]
                if len(vec_list) != EXPECTED_EMBEDDING_DIMENSION:
                    raise ValueError(
                        f"Embedding dimension mismatch: expected {EXPECTED_EMBEDDING_DIMENSION}, "
                        f"got {len(vec_list)} from model {EMBEDDING_MODEL_NAME}"
                    )
                all_embeddings.append(vec_list)

        return all_embeddings

    def embed_query(self, query: str) -> List[float]:
        """
        Embeds a single query string for semantic pgvector similarity search.
        """
        results = self.embed_texts([query])
        return results[0] if results else []

    def embed_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generates real 384-dimensional embeddings and adds 'embedding' key to each chunk.
        """
        texts = [c.get("text", "") for c in chunks]
        embeddings = self.embed_texts(texts)

        for chunk, emb in zip(chunks, embeddings):
            chunk["embedding"] = emb

        return chunks


# Global default embedder instance
default_embedder = ChunkEmbedder()


def get_embedder() -> ChunkEmbedder:
    return default_embedder
