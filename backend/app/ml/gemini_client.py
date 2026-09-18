import json
import logging
import os
import re
import time
from typing import Any, List, Optional, Tuple
from dotenv import load_dotenv

logger = logging.getLogger("app.ml.gemini_client")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

# Multi-path .env loader to ensure environment variables are loaded regardless of cwd
for _candidate_path in [
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), ".env"),
]:
    if os.path.exists(_candidate_path):
        load_dotenv(_candidate_path)
load_dotenv()

# Candidate models ordered by preference; if a free-tier quota is exhausted on one, fail over seamlessly
CONFIGURED_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
FALLBACK_MODELS = [
    CONFIGURED_MODEL,
    "gemini-2.5-flash-lite",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
]
# Deduplicate while preserving order
MODEL_CANDIDATES: List[str] = list(dict.fromkeys(FALLBACK_MODELS))

# Cached connection state
_gemini_client_instance: Optional[Any] = None
_gemini_is_connected: bool = False
_gemini_last_error: Optional[str] = None
_probe_attempted: bool = False
_cached_api_key: Optional[str] = None
_active_model_name: str = CONFIGURED_MODEL


def get_active_model_name() -> str:
    """Returns the current active working Gemini model name."""
    global _active_model_name
    return _active_model_name


def probe_gemini_connectivity(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    force_refresh: bool = False
) -> Tuple[bool, Optional[str], Optional[Any]]:
    """
    Performs a live, lightweight connectivity probe to Google Gemini API.
    Does NOT use regex, prefix checks (e.g. startswith('AIzaSy')), or format validation.
    Any non-empty string is tested with a real SDK call to confirm live API access.
    
    If the requested model is rate-limited (429), attempts fallback candidate models.
    Caches the result so subsequent calls do not repeat the probe unnecessarily.
    Returns: (is_connected: bool, error_message: Optional[str], client_instance: Optional[Any])
    """
    global _gemini_client_instance, _gemini_is_connected, _gemini_last_error
    global _probe_attempted, _cached_api_key, _active_model_name

    effective_key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY", "")

    # If already probed with same key and not forcing refresh, return cached state
    if _probe_attempted and not force_refresh:
        if effective_key == _cached_api_key:
            return _gemini_is_connected, _gemini_last_error, _gemini_client_instance

    _cached_api_key = effective_key
    _probe_attempted = True

    # Check for empty / missing key
    if not effective_key or not effective_key.strip():
        _gemini_is_connected = False
        _gemini_client_instance = None
        _gemini_last_error = "GEMINI_API_KEY is empty or missing from environment"
        logger.warning(
            "\n" + "=" * 68 + "\n"
            "[FALLBACK WARNING] [gemini_client] GEMINI_API_KEY IS MISSING!\n"
            "Reason: GEMINI_API_KEY environment variable is empty or not set.\n"
            "Action: Live Gemini calls will not be attempted until a valid key is provided.\n"
            + "=" * 68
        )
        return False, _gemini_last_error, None

    # Perform live connectivity probe using google.genai SDK
    candidate_list = [model] if model else MODEL_CANDIDATES

    try:
        from google import genai
        client = genai.Client(api_key=effective_key)
    except Exception as e:
        _gemini_client_instance = None
        _gemini_is_connected = False
        _gemini_last_error = f"genai.Client initialization failed: {type(e).__name__}: {e}"
        logger.warning(
            "\n" + "=" * 68 + "\n"
            "[FALLBACK WARNING] [gemini_client] Client initialization failed!\n"
            "Reason: %s\n"
            + "=" * 68,
            _gemini_last_error
        )
        return False, _gemini_last_error, None

    last_exc = None
    for candidate_model in candidate_list:
        try:
            logger.info(
                "[GEMINI PROBE] Initiating live connectivity probe using model '%s' (key: %s...%s)...",
                candidate_model,
                effective_key[:6] if len(effective_key) >= 6 else "key",
                effective_key[-4:] if len(effective_key) >= 4 else ""
            )

            response = client.models.generate_content(
                model=candidate_model,
                contents="ping",
                config={"max_output_tokens": 100}
            )

            probe_response_text = (response.text or "").strip()
            _gemini_client_instance = client
            _gemini_is_connected = True
            _gemini_last_error = None
            _active_model_name = candidate_model

            logger.info(
                "[GEMINI PROBE SUCCESS] Live Gemini API connection verified successfully! Model: '%s' | Response: '%s'",
                candidate_model,
                probe_response_text[:60]
            )
            return True, None, client

        except Exception as e:
            last_exc = e
            err_str = str(e)
            is_transient = any(c in err_str for c in ["429", "503", "500", "RESOURCE_EXHAUSTED", "UNAVAILABLE"])
            logger.warning(
                "\n" + "=" * 68 + "\n"
                "[FALLBACK WARNING] [gemini_client] Probe failed for model '%s'!\n"
                "Reason: %s: %s\n"
                "Action: %s\n"
                + "=" * 68,
                candidate_model,
                type(e).__name__,
                e,
                "Attempting next candidate model..." if is_transient and candidate_model != candidate_list[-1] else "No more candidate models to try."
            )
            if not is_transient:
                # If non-transient authentication failed (e.g. invalid key), no need to try other models
                break

    _gemini_client_instance = None
    _gemini_is_connected = False
    _gemini_last_error = f"{type(last_exc).__name__}: {last_exc}" if last_exc else "Probe failed"
    return False, _gemini_last_error, None


def generate_gemini_content(
    client: Any,
    contents: Any,
    config: Optional[Any] = None,
    preferred_model: Optional[str] = None
) -> Tuple[Any, str]:
    """
    Executes a content generation call against Gemini with resilient rate-limit handling.
    If the active model hits a 429 quota limit, automatically retries on an alternate candidate model.
    Returns: (response, model_used)
    """
    global _active_model_name

    initial_model = preferred_model or _active_model_name or CONFIGURED_MODEL
    candidate_order = [initial_model] + [m for m in MODEL_CANDIDATES if m != initial_model]

    last_error = None
    for model_name in candidate_order:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config
            )
            _active_model_name = model_name
            return response, model_name
        except Exception as e:
            last_error = e
            err_str = str(e)
            is_transient = any(c in err_str for c in ["429", "503", "500", "RESOURCE_EXHAUSTED", "UNAVAILABLE"])
            if is_transient and model_name != candidate_order[-1]:
                logger.warning(
                    "\n" + "=" * 68 + "\n"
                    "[FALLBACK WARNING] [gemini_client] Model '%s' hit transient error (%s: %s)!\n"
                    "Action: Seamlessly switching to alternate model candidate.\n"
                    + "=" * 68,
                    model_name,
                    type(e).__name__,
                    e
                )
                continue
            raise e

    raise last_error or RuntimeError("Gemini content generation failed across all models")


def get_gemini_client(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    force_refresh: bool = False
) -> Optional[Any]:
    """
    Returns an authenticated, verified Gemini client instance, or None if offline.
    Uses cached live connectivity status.
    """
    is_connected, _, client = probe_gemini_connectivity(
        api_key=api_key,
        model=model,
        force_refresh=force_refresh
    )
    return client if is_connected else None


def is_gemini_available(api_key: Optional[str] = None, model: Optional[str] = None) -> bool:
    """Returns True if live Gemini API is accessible."""
    is_connected, _, _ = probe_gemini_connectivity(api_key=api_key, model=model)
    return is_connected


def get_last_gemini_error() -> Optional[str]:
    """Returns the last error recorded during connectivity probe or generation."""
    return _gemini_last_error


def reset_gemini_cache() -> None:
    """Resets cached connectivity probe state (useful for tests)."""
    global _gemini_client_instance, _gemini_is_connected, _gemini_last_error
    global _probe_attempted, _cached_api_key
    _gemini_client_instance = None
    _gemini_is_connected = False
    _gemini_last_error = None
    _probe_attempted = False
    _cached_api_key = None
