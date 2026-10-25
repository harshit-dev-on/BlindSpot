"""OpenAI-compatible AI provider supporting hosted and self-hosted endpoints."""

import os
import time
from typing import Any, Dict, List, Optional
import httpx

from blindspot.ai.base import BaseAIProvider, mask_api_key
from blindspot.ai.exceptions import (
    AIAuthenticationError,
    AIConnectionError,
    AITimeoutError,
    AIProviderError,
)
from blindspot.ai.models import AIResponse, ProviderStatus


DEFAULT_OPENAI_URL = "https://api.openai.com/v1"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


class OpenAICompatibleProvider(BaseAIProvider):
    """Provider communicating with any OpenAI-compatible chat completions endpoint."""

    def __init__(
        self,
        model: str = DEFAULT_OPENAI_MODEL,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        api_key_env: Optional[str] = "OPENAI_API_KEY",
        timeout: float = 60.0,
    ) -> None:
        effective_url = base_url.strip().rstrip("/") if base_url else DEFAULT_OPENAI_URL
        super().__init__(model=model, base_url=effective_url, timeout=timeout)
        self.api_key_env = api_key_env

        # Resolve API key securely from environment variable or direct parameter
        resolved_key = None
        if api_key and api_key.strip():
            resolved_key = api_key.strip()
        elif api_key_env and os.environ.get(api_key_env):
            resolved_key = os.environ.get(api_key_env, "").strip()

        self._api_key = resolved_key

    @property
    def name(self) -> str:
        return "openai_compatible"

    @property
    def masked_api_key(self) -> str:
        """Masked string representation of the key for safe terminal display."""
        return mask_api_key(self._api_key)

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def _build_url(self, endpoint: str) -> str:
        clean_endpoint = endpoint.lstrip("/")
        if self.base_url.endswith("/v1"):
            return f"{self.base_url}/{clean_endpoint}"
        return f"{self.base_url}/v1/{clean_endpoint}"

    def check_health(self) -> ProviderStatus:
        """Test endpoint reachability and credentials."""
        start_time = time.perf_counter()
        headers = self._get_headers()
        models_url = self._build_url("models")

        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.get(models_url, headers=headers)
                latency = round((time.perf_counter() - start_time) * 1000, 2)

                if res.status_code == 401:
                    return ProviderStatus(
                        provider=self.name,
                        model=self.model,
                        base_url=self.base_url,
                        is_reachable=True,
                        model_available=False,
                        latency_ms=latency,
                        message=(
                            "Authentication failed (HTTP 401). Check that your API key is valid.\n"
                            f"Key configured from: {self.api_key_env or 'direct setting'} ({self.masked_api_key})"
                        ),
                    )

                if res.status_code == 403:
                    return ProviderStatus(
                        provider=self.name,
                        model=self.model,
                        base_url=self.base_url,
                        is_reachable=True,
                        model_available=False,
                        latency_ms=latency,
                        message=f"Access forbidden (HTTP 403). Your API key does not have permission.",
                    )

                available_models: List[str] = []
                model_found = False

                if res.status_code == 200:
                    try:
                        data = res.json()
                        models_data = data.get("data", [])
                        if isinstance(models_data, list):
                            available_models = [m.get("id", "") for m in models_data if isinstance(m, dict)]
                            model_found = self.model.lower() in [m.lower() for m in available_models]
                    except Exception:
                        pass

                # If endpoint does not support /models (returns 404 or 405), we treat it as reachable
                # and assume model is valid since custom proxy endpoints frequently omit /models.
                if res.status_code in (404, 405) or not available_models:
                    model_found = True

                return ProviderStatus(
                    provider=self.name,
                    model=self.model,
                    base_url=self.base_url,
                    is_reachable=True,
                    model_available=model_found,
                    latency_ms=latency,
                    available_models=available_models if available_models else None,
                    message=(
                        f"Connected to {self.base_url} ({latency}ms). "
                        f"Model: {self.model} (API Key: {self.masked_api_key})."
                    ),
                )

        except httpx.ConnectError:
            return ProviderStatus(
                provider=self.name,
                model=self.model,
                base_url=self.base_url,
                is_reachable=False,
                model_available=False,
                message=f"Could not connect to API server at {self.base_url}. Verify the URL and network connection.",
            )
        except httpx.TimeoutException:
            return ProviderStatus(
                provider=self.name,
                model=self.model,
                base_url=self.base_url,
                is_reachable=False,
                model_available=False,
                message=f"Request to {self.base_url} timed out after {self.timeout}s.",
            )
        except Exception as exc:
            return ProviderStatus(
                provider=self.name,
                model=self.model,
                base_url=self.base_url,
                is_reachable=False,
                model_available=False,
                message=f"Error checking endpoint health: {exc}",
            )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        format_json: bool = False,
    ) -> AIResponse:
        """Send chat completion request to an OpenAI-compatible endpoint."""
        chat_url = self._build_url("chat/completions")
        headers = self._get_headers()

        messages = []
        if system_prompt and system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt.strip()})
        messages.append({"role": "user", "content": prompt.strip()})

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }

        # Try with response_format first if requested
        if format_json:
            payload["response_format"] = {"type": "json_object"}

        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(chat_url, headers=headers, json=payload)

                # Gracefully handle providers that do not support response_format (e.g. 400 Bad Request)
                if format_json and res.status_code == 400 and "response_format" in res.text:
                    payload.pop("response_format", None)
                    res = client.post(chat_url, headers=headers, json=payload)

                if res.status_code == 401:
                    raise AIAuthenticationError(
                        "Authentication failed: Invalid or missing API key.",
                        provider=self.name,
                        suggestion=(
                            f"Ensure the '{self.api_key_env or 'OPENAI_API_KEY'}' environment variable "
                            "is set with a valid API key."
                        ),
                    )

                if res.status_code != 200:
                    raise AIProviderError(
                        f"API request failed with HTTP {res.status_code}: {res.text}",
                        provider=self.name,
                    )

                data = res.json()
                choices = data.get("choices", [])
                if not choices:
                    raise AIProviderError(
                        "API returned an empty choices list.",
                        provider=self.name,
                    )

                content = choices[0].get("message", {}).get("content", "")
                usage = data.get("usage")

                return AIResponse(
                    content=content,
                    model=data.get("model", self.model),
                    provider=self.name,
                    usage=usage,
                    raw_response=data,
                )

        except httpx.ConnectError as exc:
            raise AIConnectionError(
                f"Cannot connect to {self.base_url}.",
                provider=self.name,
                suggestion="Verify that the base_url is reachable and your internet connection is active.",
            ) from exc
        except httpx.TimeoutException as exc:
            raise AITimeoutError(
                f"Request to {self.base_url} timed out after {self.timeout}s.",
                provider=self.name,
                suggestion="Increase the timeout in your configuration.",
            ) from exc
        except (AIAuthenticationError, AIProviderError, AIConnectionError, AITimeoutError):
            raise
        except Exception as exc:
            raise AIProviderError(
                f"Unexpected error communicating with OpenAI-compatible API: {exc}",
                provider=self.name,
            ) from exc
