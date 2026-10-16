"""Dedicated AI adapter wrapping LiteLLM for universal model access."""

import os
import time
from typing import Any, Dict, List, Optional
import httpx
import litellm

from blindspot.ai.base import BaseAIProvider
from blindspot.ai.exceptions import (
    AIAuthenticationError,
    AIConnectionError,
    AIModelNotFoundError,
    AITimeoutError,
    AIProviderError,
)
from blindspot.ai.models import AIResponse, ProviderStatus
from blindspot.ai.providers.openai_compatible import mask_api_key

# Suppress noisy debug logs and drop unsupported provider parameters automatically
import logging
logging.getLogger("LiteLLM").setLevel(logging.ERROR)
litellm.suppress_debug_info = True
litellm.drop_params = True


DEFAULT_PROVIDER_MODELS: Dict[str, str] = {
    "ollama": "gemma4",
    "gemini": "gemini-3.5-flash-lite",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-sonnet-20241022",
    "openrouter": "meta-llama/llama-3.1-8b-instruct",
    "custom": "default",
    "openai_compatible": "gpt-4o-mini",
}

DEFAULT_KEY_ENVS: Dict[str, str] = {
    "gemini": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "custom": "CUSTOM_API_KEY",
    "openai_compatible": "OPENAI_API_KEY",
}

DEFAULT_BASE_URLS: Dict[str, str] = {
    "ollama": "http://localhost:11434",
    "openai": "https://api.openai.com/v1",
    "openrouter": "https://openrouter.ai/api/v1",
}

CURATED_MODELS: Dict[str, List[str]] = {
    "ollama": ["gemma4", "llama3.2", "mistral", "phi3", "qwen2.5"],
    "gemini": ["gemini-3.5-flash-lite", "gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash"],
    "openai": ["gpt-4o-mini", "gpt-4o", "o3-mini", "gpt-4-turbo"],
    "anthropic": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
    "openrouter": [
        "meta-llama/llama-3.1-8b-instruct",
        "google/gemini-flash-1.5",
        "anthropic/claude-3.5-sonnet",
        "mistralai/mistral-7b-instruct",
    ],
    "custom": [],
    "openai_compatible": [],
}


class UnifiedAIAdapter(BaseAIProvider):
    """Universal AI provider adapter wrapping LiteLLM behind the BlindSpot AI interface."""

    def __init__(
        self,
        provider: str = "ollama",
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        api_key_env: Optional[str] = None,
        timeout: float = 60.0,
    ) -> None:
        self._provider_name = provider.lower().strip()
        default_model = DEFAULT_PROVIDER_MODELS.get(self._provider_name, "gemma4")
        chosen_model = model.strip() if model else default_model

        super().__init__(model=chosen_model, base_url=base_url, timeout=timeout)

        # Resolve API key environment variable name
        self.api_key_env = api_key_env or DEFAULT_KEY_ENVS.get(self._provider_name)

        # Resolve key securely (Env var preferred > explicit parameter)
        resolved_key = None
        if api_key and api_key.strip():
            resolved_key = api_key.strip()
        elif self.api_key_env and os.environ.get(self.api_key_env):
            resolved_key = os.environ.get(self.api_key_env, "").strip()

        self._api_key = resolved_key

    @property
    def name(self) -> str:
        return self._provider_name

    @property
    def masked_api_key(self) -> str:
        return mask_api_key(self._api_key)

    @property
    def litellm_model(self) -> str:
        """Translate model string to LiteLLM router format."""
        m = self.model

        if self._provider_name == "ollama":
            return m if m.startswith("ollama/") or m.startswith("ollama_chat/") else f"ollama/{m}"
        if self._provider_name == "gemini":
            return m if m.startswith("gemini/") else f"gemini/{m}"
        if self._provider_name == "anthropic":
            return m if m.startswith("anthropic/") else f"anthropic/{m}"
        if self._provider_name == "openrouter":
            return m if m.startswith("openrouter/") else f"openrouter/{m}"
        if self._provider_name in ("custom", "openai_compatible"):
            return m if m.startswith("openai/") else f"openai/{m}"
        if self._provider_name == "openai":
            return m if m.startswith("openai/") else f"openai/{m}"

        return m

    def check_health(self) -> ProviderStatus:
        """Test endpoint connectivity, authentication, and model availability."""
        # Specialized local health probe for Ollama
        if self._provider_name == "ollama":
            return self._check_ollama_health()

        # Cloud and custom endpoints: perform quick verification
        start_time = time.perf_counter()

        # Validate presence of API key if provider requires it
        requires_key = self._provider_name in ("gemini", "openai", "anthropic", "openrouter")
        if requires_key and not self._api_key:
            return ProviderStatus(
                provider=self.name,
                model=self.model,
                base_url=self.base_url or "(hosted cloud)",
                is_reachable=False,
                model_available=False,
                message=(
                    f"Missing API key for {self.name.upper()}.\n"
                    f"Set the '{self.api_key_env}' environment variable or run 'blindspot setup'."
                ),
            )

        try:
            # Lightweight probe
            kwargs: Dict[str, Any] = {
                "model": self.litellm_model,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 1,
                "timeout": min(self.timeout, 15.0),
            }
            if self.base_url:
                kwargs["api_base"] = self.base_url
            if self._api_key:
                kwargs["api_key"] = self._api_key

            litellm.completion(**kwargs)
            latency = round((time.perf_counter() - start_time) * 1000, 2)

            return ProviderStatus(
                provider=self.name,
                model=self.model,
                base_url=self.base_url or "(hosted cloud)",
                is_reachable=True,
                model_available=True,
                latency_ms=latency,
                message=f"Connected to {self.name.upper()}. Model '{self.model}' is ready ({latency}ms).",
            )

        except litellm.exceptions.AuthenticationError as exc:
            return ProviderStatus(
                provider=self.name,
                model=self.model,
                base_url=self.base_url or "(hosted cloud)",
                is_reachable=True,
                model_available=False,
                message=f"Authentication failed: {exc}. Verify your API key in '{self.api_key_env}'.",
            )
        except litellm.exceptions.NotFoundError as exc:
            return ProviderStatus(
                provider=self.name,
                model=self.model,
                base_url=self.base_url or "(hosted cloud)",
                is_reachable=True,
                model_available=False,
                message=f"Model '{self.model}' was not found on {self.name}: {exc}",
            )
        except litellm.exceptions.APIConnectionError as exc:
            return ProviderStatus(
                provider=self.name,
                model=self.model,
                base_url=self.base_url or "(hosted cloud)",
                is_reachable=False,
                model_available=False,
                message=f"Connection failed: {exc}. Check your internet connection or endpoint URL.",
            )
        except litellm.exceptions.Timeout as exc:
            return ProviderStatus(
                provider=self.name,
                model=self.model,
                base_url=self.base_url or "(hosted cloud)",
                is_reachable=False,
                model_available=False,
                message=f"Request to {self.name} timed out: {exc}",
            )
        except Exception as exc:
            return ProviderStatus(
                provider=self.name,
                model=self.model,
                base_url=self.base_url or "(hosted cloud)",
                is_reachable=False,
                model_available=False,
                message=f"Provider test error: {exc}",
            )

    def _check_ollama_health(self) -> ProviderStatus:
        """Fast local probe of Ollama tags."""
        base_url = self.base_url or DEFAULT_BASE_URLS["ollama"]
        tags_url = f"{base_url.rstrip('/')}/api/tags"
        start_time = time.perf_counter()

        try:
            with httpx.Client(timeout=min(self.timeout, 10.0)) as client:
                res = client.get(tags_url)
                latency = round((time.perf_counter() - start_time) * 1000, 2)

                if res.status_code != 200:
                    return ProviderStatus(
                        provider=self.name,
                        model=self.model,
                        base_url=base_url,
                        is_reachable=False,
                        model_available=False,
                        message=f"Ollama returned HTTP {res.status_code}",
                    )

                data = res.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                target = self.model.lower()
                found = any(target == m.lower() or m.lower().startswith(f"{target}:") for m in models)

                if not found:
                    return ProviderStatus(
                        provider=self.name,
                        model=self.model,
                        base_url=base_url,
                        is_reachable=True,
                        model_available=False,
                        latency_ms=latency,
                        available_models=models,
                        message=(
                            f"Ollama is running, but model '{self.model}' is not installed.\n"
                            f"Installed models: {', '.join(models) if models else 'None'}.\n"
                            f"Run 'ollama pull {self.model}' to download it."
                        ),
                    )

                return ProviderStatus(
                    provider=self.name,
                    model=self.model,
                    base_url=base_url,
                    is_reachable=True,
                    model_available=True,
                    latency_ms=latency,
                    available_models=models,
                    message=f"Connected to Ollama. Model '{self.model}' is ready ({latency}ms).",
                )
        except httpx.ConnectError:
            return ProviderStatus(
                provider=self.name,
                model=self.model,
                base_url=base_url,
                is_reachable=False,
                model_available=False,
                message=(
                    f"Could not connect to Ollama server at {base_url}.\n"
                    "Ensure Ollama is installed and running ('ollama serve')."
                ),
            )
        except Exception as exc:
            return ProviderStatus(
                provider=self.name,
                model=self.model,
                base_url=base_url,
                is_reachable=False,
                model_available=False,
                message=f"Error connecting to Ollama: {exc}",
            )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        format_json: bool = False,
    ) -> AIResponse:
        """Execute text completion via LiteLLM adapter."""
        messages: List[Dict[str, str]] = []
        if system_prompt and system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt.strip()})
        messages.append({"role": "user", "content": prompt.strip()})

        requires_key = self._provider_name in ("gemini", "openai", "anthropic", "openrouter")
        if requires_key and not self._api_key:
            raise AIAuthenticationError(
                f"Missing API key for {self.name.upper()}.",
                provider=self.name,
                suggestion=f"Set the {self.api_key_env} environment variable or run 'blindspot setup'.",
            )

        kwargs: Dict[str, Any] = {
            "model": self.litellm_model,
            "messages": messages,
            "temperature": temperature,
            "timeout": self.timeout,
        }

        if self.base_url:
            kwargs["api_base"] = self.base_url
        if self._api_key:
            kwargs["api_key"] = self._api_key
        if format_json:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            resp = litellm.completion(**kwargs)

            # Extract content safely
            choices = getattr(resp, "choices", [])
            content = choices[0].message.content if choices else ""
            usage = dict(resp.usage) if getattr(resp, "usage", None) else None

            return AIResponse(
                content=content or "",
                model=getattr(resp, "model", self.model),
                provider=self.name,
                usage=usage,
                raw_response=dict(resp) if hasattr(resp, "keys") else None,
            )

        except litellm.exceptions.AuthenticationError as exc:
            raise AIAuthenticationError(
                f"Authentication failed for {self.name.upper()}: {exc}",
                provider=self.name,
                suggestion=f"Check your API key in '{self.api_key_env}'.",
            ) from exc
        except litellm.exceptions.NotFoundError as exc:
            raise AIModelNotFoundError(
                f"Model '{self.model}' not found on {self.name}: {exc}",
                provider=self.name,
                suggestion=f"Verify model name or run 'blindspot model list --provider {self.name}'.",
            ) from exc
        except litellm.exceptions.APIConnectionError as exc:
            raise AIConnectionError(
                f"Cannot connect to {self.name}: {exc}",
                provider=self.name,
                suggestion="Verify network connection or server endpoint URL.",
            ) from exc
        except litellm.exceptions.Timeout as exc:
            raise AITimeoutError(
                f"Request to {self.name} timed out after {self.timeout}s: {exc}",
                provider=self.name,
            ) from exc
        except (AIAuthenticationError, AIModelNotFoundError, AIConnectionError, AITimeoutError):
            raise
        except Exception as exc:
            raise AIProviderError(
                f"AI generation error on {self.name}: {exc}",
                provider=self.name,
            ) from exc


def get_models_for_provider(
    provider: str, base_url: Optional[str] = None
) -> List[str]:
    """Retrieve discoverable or curated models for a given provider."""
    p_clean = provider.lower().strip()
    if p_clean == "openai_compatible":
        p_clean = "custom"

    # For Ollama: try to dynamically discover models downloaded on local server
    if p_clean == "ollama":
        target_url = base_url or DEFAULT_BASE_URLS["ollama"]
        tags_url = f"{target_url.rstrip('/')}/api/tags"
        try:
            with httpx.Client(timeout=4.0) as client:
                res = client.get(tags_url)
                if res.status_code == 200:
                    models = [m.get("name", "") for m in res.json().get("models", [])]
                    if models:
                        return models
        except Exception:
            pass

    # Return curated models list
    return CURATED_MODELS.get(p_clean, [])
