"""Small Sarvam chat-completions client used by the grounded document workflows."""

import json
import logging
import os
from typing import Any, Dict

import httpx
from dotenv import load_dotenv
from app.errors import SarvamUnavailableError

logger = logging.getLogger(__name__)

# Multi-path .env loader
for _candidate_path in [
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), ".env"),
]:
    if os.path.exists(_candidate_path):
        load_dotenv(_candidate_path)
load_dotenv()


class SarvamClient:
    @property
    def api_key(self) -> str:
        return os.getenv("SARVAM_API_KEY", "").strip()

    @property
    def base_url(self) -> str:
        return os.getenv("SARVAM_BASE_URL", "https://api.sarvam.ai/v1").rstrip("/")

    @property
    def model(self) -> str:
        return os.getenv("SARVAM_MODEL", "sarvam-m")

    def complete_json(self, prompt: str) -> Dict[str, Any]:
        key = self.api_key
        if not key or key.startswith("your_"):
            raise SarvamUnavailableError("SARVAM_API_KEY is not configured or is a placeholder.")
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "api-subscription-key": key,
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "Return only valid JSON. Never use markdown fences."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.1,
                },
                timeout=45.0,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            if isinstance(content, list):
                content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
            clean = str(content).removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            return json.loads(clean)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise SarvamUnavailableError("Sarvam returned an invalid structured response.") from exc
        except httpx.HTTPStatusError as exc:
            raise SarvamUnavailableError(f"Sarvam API error (HTTP {exc.response.status_code}): {exc.response.text}") from exc
        except httpx.HTTPError as exc:
            raise SarvamUnavailableError(f"Sarvam network error: {exc}") from exc


sarvam_client = SarvamClient()
