import os
import logging
from typing import Optional
from app.db import get_db

logger = logging.getLogger(__name__)

DEFAULT_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "InsuranceFiles")
LOCAL_STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "storage")
REQUIRE_REMOTE_STORAGE = os.getenv("REQUIRE_REMOTE_STORAGE", "").strip().lower() in {"1", "true", "yes"}
REMOTE_STORAGE_CONFIGURED = bool(
    os.getenv("SUPABASE_URL") and (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY"))
)


class StorageManager:
    """
    Object storage manager for uploaded document files.
    Production deployments should set REQUIRE_REMOTE_STORAGE=true so an upload never
    succeeds when it only exists on Render's ephemeral filesystem.
    """

    def __init__(self, bucket_name: Optional[str] = None):
        self.bucket_name = bucket_name or DEFAULT_BUCKET
        self.local_dir = LOCAL_STORAGE_DIR
        os.makedirs(self.local_dir, exist_ok=True)

    def store_file(self, doc_id: str, filename: str, file_bytes: bytes) -> str:
        """
        Stores file bytes into object storage.
        Returns the canonical storage path (e.g. 'documents/{doc_id}/{filename}').
        """
        clean_filename = os.path.basename(filename) or "uploaded_document.pdf"
        storage_path = f"documents/{doc_id}/{clean_filename}"

        # Local copies are useful for development but are not durable on Render.
        local_target_path = os.path.join(self.local_dir, "documents", doc_id, clean_filename)
        os.makedirs(os.path.dirname(local_target_path), exist_ok=True)
        try:
            with open(local_target_path, "wb") as f:
                f.write(file_bytes)
        except Exception as e:
            logger.warning("Failed to write to local storage copy: %s", e)

        # Upload to Supabase Storage. Log critical warning on failure but never
        # crash the upload — the ingestion pipeline processes bytes in-memory,
        # not from the storage path, so text extraction always works regardless.
        try:
            db = get_db()
            if hasattr(db, "storage"):
                try:
                    db.storage.from_(self.bucket_name).upload(
                        path=storage_path,
                        file=file_bytes,
                        file_options={"content-type": "application/pdf", "upsert": "true"}
                    )
                    logger.info("Successfully uploaded %s to Supabase Storage bucket %s", storage_path, self.bucket_name)
                    return storage_path
                except Exception as upload_err:
                    if REQUIRE_REMOTE_STORAGE and REMOTE_STORAGE_CONFIGURED:
                        # Log at critical level but do NOT raise — the pipeline can still
                        # process and analyze the document from in-memory bytes.
                        logger.critical(
                            "Supabase Storage upload FAILED (bucket='%s', path='%s'). "
                            "Document will still be processed but file is not persisted remotely. "
                            "Check bucket exists and service role key has storage permissions. Error: %s",
                            self.bucket_name, storage_path, upload_err
                        )
                    else:
                        logger.warning(
                            "Supabase storage upload failed; continuing with local persistence only: %s",
                            upload_err,
                        )
        except Exception as e:
            logger.warning("Supabase client storage access skipped; using local persistence only: %s", e)

        if REQUIRE_REMOTE_STORAGE and not REMOTE_STORAGE_CONFIGURED:
            logger.warning(
                "REQUIRE_REMOTE_STORAGE is enabled but Supabase is not configured; continuing with local file storage for this deployment."
            )
        return storage_path

    def retrieve_file(self, storage_path: str) -> Optional[bytes]:
        """
        Retrieves raw bytes from storage path.
        """
        # Try local storage first
        local_path = os.path.join(self.local_dir, storage_path.replace("/", os.sep))
        if os.path.exists(local_path):
            with open(local_path, "rb") as f:
                return f.read()

        # Try Supabase storage
        try:
            db = get_db()
            if hasattr(db, "storage"):
                data = db.storage.from_(self.bucket_name).download(storage_path)
                return data
        except Exception as e:
            logger.warning("Could not download %s from Supabase storage: %s", storage_path, e)

        return None
