import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EXPECTED_EMBEDDING_DIMENSION = 384

# Global cached model instance to ensure model is loaded only once
_sentence_transformer_model = None


def get_embedding_model(timeout_seconds: int = 30):
    """
    Returns the singleton SentenceTransformer instance.
    Prioritizes local cache (local_files_only=True, ~0.25s load), preventing
    silent network hangs on Hugging Face Hub connectivity checks.
    """
    global _sentence_transformer_model
    if _sentence_transformer_model is None:
        import time
        t0 = time.time()
        logger.info("Initializing SentenceTransformer model '%s'...", EMBEDDING_MODEL_NAME)
        from sentence_transformers import SentenceTransformer
        try:
            # Fast offline-first path: load directly from pre-cached files
            _sentence_transformer_model = SentenceTransformer(EMBEDDING_MODEL_NAME, local_files_only=True)
            dt = time.time() - t0
            logger.info("SentenceTransformer model '%s' loaded from local cache in %.2fs.", EMBEDDING_MODEL_NAME, dt)
        except Exception as local_err:
            logger.warning(
                "Local cache load for '%s' was not available (%s). Downloading model from Hugging Face Hub (timeout: %ss)...",
                EMBEDDING_MODEL_NAME, local_err, timeout_seconds
            )
            try:
                _sentence_transformer_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
                dt = time.time() - t0
                logger.info("SentenceTransformer model '%s' downloaded and loaded in %.2fs.", EMBEDDING_MODEL_NAME, dt)
            except Exception as download_err:
                logger.error(
                    "CRITICAL: Failed to download or initialize SentenceTransformer model '%s': %s",
                    EMBEDDING_MODEL_NAME, download_err
                )
                raise RuntimeError(
                    f"SentenceTransformer embedding model '{EMBEDDING_MODEL_NAME}' failed to load: {download_err}"
                ) from download_err
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
        Generates real embeddings from actual chunk text.
        Never generates fake, synthetic, or hash-based vectors.
        """
        if not texts:
            return []

        model = get_embedding_model()
        all_embeddings: List[List[float]] = []

        import time
        t0 = time.time()
        logger.info("Computing 384-d embeddings for %d texts (batch_size=%d)...", len(texts), self.batch_size)

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            # normalize_embeddings=True produces unit vectors for cosine similarity
            vectors = model.encode(batch, convert_to_numpy=True, normalize_embeddings=True)
            for vec in vectors:
                vec_list = [float(x) for x in vec]
                if len(vec_list) != EXPECTED_EMBEDDING_DIMENSION:
                    raise ValueError(
                        f"Embedding dimension mismatch: expected {EXPECTED_EMBEDDING_DIMENSION}, "
                        f"got {len(vec_list)} from model {EMBEDDING_MODEL_NAME}"
                    )
                all_embeddings.append(vec_list)

        dt = time.time() - t0
        logger.info("Generated %d embeddings successfully in %.2fs.", len(all_embeddings), dt)
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
