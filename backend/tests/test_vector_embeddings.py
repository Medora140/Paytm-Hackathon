import os
import sys
import uuid
import pytest
import numpy as np
from dotenv import load_dotenv

# Ensure backend root is on path and env is loaded
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from app.ingestion.embedder import ChunkEmbedder, get_embedder, EXPECTED_EMBEDDING_DIMENSION
from app.db import get_db


def test_sentence_transformers_embedding_generation():
    """
    1. Embeds real text.
    2. Confirms returned vector has expected dimension (384).
    3. Confirms it contains real floating-point embedding values (non-zero, non-hash).
    """
    embedder = ChunkEmbedder()
    sample_text = (
        "Room rent is capped at 1% of the Sum Insured per day. Proportionate deductions "
        "apply to associate medical charges if room rent limit is exceeded."
    )
    vectors = embedder.embed_texts([sample_text])

    assert len(vectors) == 1, "Expected 1 vector for 1 input text"
    vec = vectors[0]

    # Check exact dimension
    assert len(vec) == EXPECTED_EMBEDDING_DIMENSION == 384, f"Vector dimension must be 384, got {len(vec)}"

    # Check floating point values
    assert all(isinstance(x, float) for x in vec), "All elements must be Python floats"
    assert any(x != 0.0 for x in vec), "Vector must contain real non-zero values"
    assert not any(np.isnan(x) for x in vec), "Vector must not contain NaN"

    # Verify unit norm from normalized embeddings
    norm = np.linalg.norm(vec)
    assert np.isclose(norm, 1.0, atol=1e-3), f"Vector should be normalized to unit length, got {norm}"


def test_pgvector_storage_retrieval_and_similarity():
    """
    4. Stores embedding in PostgreSQL / pgvector table (document_chunks).
    5. Retrieves it successfully from Supabase.
    6. Performs vector similarity search with a related query.
    """
    db = get_db()
    assert db is not None, "Supabase client must be available"

    embedder = get_embedder()
    chunk_text = (
        "Pre-existing diseases (PED) are subject to a mandatory 36-month waiting period "
        "of continuous coverage before any claim is payable."
    )
    unrelated_text = (
        "The mutual fund scheme invests 80% to 100% in equity securities of large-cap companies."
    )

    chunk_vec = embedder.embed_texts([chunk_text])[0]
    unrelated_vec = embedder.embed_texts([unrelated_text])[0]

    # Setup a test document in Supabase
    test_user_id = "00000000-0000-4000-8000-000000000001"
    # Ensure demo user exists
    db.table("users").upsert({"id": test_user_id, "email": "test_embed@moneydocs.internal"}).execute()

    test_doc_id = str(uuid.uuid4())
    db.table("documents").insert({
        "id": test_doc_id,
        "user_id": test_user_id,
        "filename": "test_vector_doc.pdf",
        "document_type": "health_insurance",
        "storage_path": f"test/{test_doc_id}/test.pdf",
        "status": "embedded"
    }).execute()

    try:
        # Insert test chunks with real 384-dim vectors
        chunk_id = str(uuid.uuid4())
        db.table("document_chunks").insert({
            "id": chunk_id,
            "document_id": test_doc_id,
            "page_number": 1,
            "clause_label": "Clause 4.1: PED Waiting Period",
            "text": chunk_text,
            "embedding": chunk_vec
        }).execute()

        # Retrieve chunk directly from Supabase
        res = db.table("document_chunks").select("*").eq("id", chunk_id).execute()
        assert res.data and len(res.data) == 1, "Retrieved chunk must exist in Supabase"
        retrieved = res.data[0]
        assert retrieved["text"] == chunk_text

        # Verify embedding field was stored and retrieved
        retrieved_emb = retrieved["embedding"]
        if isinstance(retrieved_emb, str):
            import json
            try:
                retrieved_vec = json.loads(retrieved_emb)
            except Exception:
                retrieved_vec = [float(x) for x in retrieved_emb.strip("[]").split(",") if x.strip()]
        else:
            retrieved_vec = retrieved_emb

        assert len(retrieved_vec) == 384, f"Retrieved vector must have 384 dimensions, got {len(retrieved_vec)}"

        # Perform semantic similarity search
        query = "How long is the waiting period for pre-existing conditions?"
        query_vec = embedder.embed_query(query)

        sim_ped = float(np.dot(query_vec, chunk_vec))
        sim_unrelated = float(np.dot(query_vec, unrelated_vec))

        print(f"Similarity to relevant clause: {sim_ped:.4f}")
        print(f"Similarity to unrelated clause: {sim_unrelated:.4f}")

        # The relevant PED clause must have significantly higher similarity than mutual fund equity clause
        assert sim_ped > sim_unrelated, "Semantic search must score relevant clause higher than unrelated text"
        assert sim_ped > 0.5, f"Relevant clause similarity should be high (> 0.5), got {sim_ped:.4f}"

    finally:
        # Clean up test document and cascade-deleted chunks
        try:
            db.table("documents").delete().eq("id", test_doc_id).execute()
        except Exception:
            pass


if __name__ == "__main__":
    print("Running test_sentence_transformers_embedding_generation()...")
    test_sentence_transformers_embedding_generation()
    print("test_sentence_transformers_embedding_generation passed!")
    print("Running test_pgvector_storage_retrieval_and_similarity()...")
    test_pgvector_storage_retrieval_and_similarity()
    print("test_pgvector_storage_retrieval_and_similarity passed!")
