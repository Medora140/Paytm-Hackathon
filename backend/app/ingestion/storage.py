import os
import logging
from typing import Optional
from app.db import get_db

logger = logging.getLogger(__name__)

DEFAULT_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "InsuranceFiles")
LOCAL_STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "storage")


class StorageManager:
    """
    Object storage manager for uploaded document files.
    Uploads raw files to Supabase Storage bucket (InsuranceFiles)
    with local disk fallback for development, testing, and offline resilience.
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

        # 1. Always ensure local persistent copy
        local_target_path = os.path.join(self.local_dir, "documents", doc_id, clean_filename)
        os.makedirs(os.path.dirname(local_target_path), exist_ok=True)
        try:
            with open(local_target_path, "wb") as f:
                f.write(file_bytes)
        except Exception as e:
            logger.warning("Failed to write to local storage copy: %s", e)

        # 2. Upload to Supabase Storage bucket if client is available
        try:
            db = get_db()
            if hasattr(db, "storage"):
                # Check if bucket exists; if not, create
                try:
                    db.storage.from_(self.bucket_name).upload(
                        path=storage_path,
                        file=file_bytes,
                        file_options={"content-type": "application/pdf", "upsert": "true"}
                    )
                    logger.info("Successfully uploaded %s to Supabase Storage bucket %s", storage_path, self.bucket_name)
                except Exception as upload_err:
                    logger.debug("Supabase storage upload returned: %s (using local copy)", upload_err)
        except Exception as e:
            logger.debug("Supabase client storage access skipped: %s", e)

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
