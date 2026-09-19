import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging
import json

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

from app.ingestion.pipeline import get_ingestion_pipeline
from app.db import get_db

def main():
    doc_id = "1c7b0f08-c9dc-46f6-9a93-54e5c25117c2"
    print(f"\n====================================================================")
    print(f"=== BUG 1: Re-running Ingestion for Document '{doc_id}' ===")
    print(f"====================================================================\n")

    pipeline = get_ingestion_pipeline()
    result = pipeline.process_document(doc_id=doc_id)

    print(f"\n>>> INGESTION COMPLETION STATUS: {result['status']} | Chunks: {result['chunks_count']} | Issuer: {result['issuer_name']}")

    # Direct Supabase Query Verification
    db = get_db()
    chunks_res = db.table("document_chunks").select("id, page_number, clause_label, embedding").eq("document_id", doc_id).limit(5).execute()
    count_res = db.table("document_chunks").select("count", count="exact").eq("document_id", doc_id).execute()

    print(f"\n====================================================================")
    print(f"=== DIRECT SUPABASE QUERY VERIFICATION ===")
    print(f"====================================================================")
    print(f"Total Chunks in Supabase for '{doc_id}': {count_res.count}")
    for idx, c in enumerate(chunks_res.data, start=1):
        raw_emb = c.get("embedding")
        if isinstance(raw_emb, str):
            try:
                emb_vec = json.loads(raw_emb)
            except Exception:
                emb_vec = [float(x) for x in raw_emb.strip("[]").split(",") if x.strip()]
        elif isinstance(raw_emb, list):
            emb_vec = raw_emb
        else:
            emb_vec = []
        print(f"Chunk #{idx} ID: {c['id']} | Page: {c['page_number']} | Clause: {c.get('clause_label')} | Embedding Dimension: {len(emb_vec)} | Non-null: {len(emb_vec) == 384}")

    doc_res = db.table("documents").select("id, status, filename").eq("id", doc_id).execute()
    print(f"\nDocument Record in Supabase: {doc_res.data[0]}")
    assert count_res.count > 0, "No chunks found in Supabase!"
    assert len(emb_vec) == 384, "Embedding vector length mismatch!"
    print("\n>>> BUG 1 VERIFICATION COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
