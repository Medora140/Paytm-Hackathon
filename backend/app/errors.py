class ChunksNotFoundError(Exception):
    """Raised when document chunks cannot be loaded from repository or Supabase."""

    def __init__(self, document_id: str, reason: str):
        self.document_id = document_id
        self.reason = reason
        super().__init__(
            f"No extracted chunks found for document '{document_id}'. {reason}"
        )


class GeminiUnavailableError(Exception):
    """Raised when Gemini is required but the live API cannot be used."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Gemini is unavailable: {reason}")
