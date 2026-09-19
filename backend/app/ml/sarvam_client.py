"""Small Sarvam chat-completions client used by the grounded document workflows."""

import json
import os
from typing import Any, Dict

import httpx
from app.errors import SarvamUnavailableError


class SarvamClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("SARVAM_API_KEY", "").strip()
        self.base_url = os.getenv("SARVAM_BASE_URL", "https://api.sarvam.ai/v1").rstrip("/")
        self.model = os.getenv("SARVAM_MODEL", "sarvam-m")

    def complete_json(self, prompt: str) -> Dict[str, Any]:
        if not self.api_key:
            raise SarvamUnavailableError("SARVAM_API_KEY is not configured.")
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={"api-subscription-key": self.api_key, "Content-Type": "application/json"},
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
        except httpx.HTTPError as exc:
            raise SarvamUnavailableError(f"Sarvam request failed: {exc}") from exc


sarvam_client = SarvamClient()
