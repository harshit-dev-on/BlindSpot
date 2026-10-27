"""Abstract base class and common logic for all AI providers."""

from abc import ABC, abstractmethod
import json
import re
from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel, ValidationError

from blindspot.ai.exceptions import AIStructuredOutputError
from blindspot.ai.models import AIResponse, ProviderStatus

T = TypeVar("T", bound=BaseModel)


def extract_json_string(text: str) -> str:
    """Extract a JSON substring from a model response.

    Handles raw JSON, markdown-fenced code blocks (```json ... ```),
    and responses with leading or trailing explanatory text.

    Args:
        text: Raw text string from the model.

    Returns:
        Extracted candidate JSON string.
    """
    clean_text = text.strip()

    # 1. Check for fenced code blocks with ```json or ```
    fenced_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean_text, re.IGNORECASE)
    if fenced_match:
        return fenced_match.group(1).strip()

    # 2. Look for outer JSON object {...} or array [...]
    first_brace = clean_text.find("{")
    last_brace = clean_text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return clean_text[first_brace : last_brace + 1].strip()

    first_bracket = clean_text.find("[")
    last_bracket = clean_text.rfind("]")
    if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
        return clean_text[first_bracket : last_bracket + 1].strip()

    return clean_text


class BaseAIProvider(ABC):
    """Abstract interface that every AI provider must implement."""

    def __init__(self, model: str, base_url: Optional[str] = None, timeout: float = 60.0) -> None:
        self._model = model.strip()
        self._base_url = base_url.strip().rstrip("/") if base_url else ""
        self._timeout = timeout

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique provider identifier (e.g. 'ollama', 'openai_compatible')."""
        pass

    @property
    def model(self) -> str:
        """Configured model name or identifier."""
        return self._model

    @model.setter
    def model(self, value: str) -> None:
        self._model = value.strip()

    @property
    def base_url(self) -> str:
        """API endpoint base URL."""
        return self._base_url

    @property
    def timeout(self) -> float:
        """Timeout in seconds for API requests."""
        return self._timeout

    @abstractmethod
    def check_health(self) -> ProviderStatus:
        """Test endpoint reachability and model availability."""
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        format_json: bool = False,
        image_b64: Optional[str] = None,
    ) -> AIResponse:
        """Send a prompt to the model and return its text response."""
        pass

    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_retries: int = 1,
        image_b64: Optional[str] = None,
    ) -> T:
        """Request structured output complying with a Pydantic model schema.

        Validates the output against the schema and handles retries if the model
        produces malformed JSON.

        Args:
            prompt: User instructions and input data.
            schema: Pydantic model class defining the expected response structure.
            system_prompt: Optional overarching system instructions.
            temperature: Sampling temperature (default 0.2 for structured output).
            max_retries: Number of correction attempts if parsing fails.
            image_b64: Optional base64-encoded screenshot image for multimodal visual inference.

        Returns:
            Validated instance of the provided Pydantic model schema.

        Raises:
            AIStructuredOutputError: If the model output cannot be parsed into the schema.
        """
        json_schema_str = json.dumps(schema.model_json_schema(), indent=2)
        structural_instructions = (
            f"You MUST respond ONLY with a valid JSON object matching this JSON Schema:\n"
            f"```json\n{json_schema_str}\n```\n"
            "Do NOT include any commentary, explanations, or text outside the JSON object."
        )

        effective_system = (
            f"{system_prompt.strip()}\n\n{structural_instructions}"
            if system_prompt and system_prompt.strip()
            else structural_instructions
        )

        current_prompt = prompt
        attempts = 0

        while attempts <= max_retries:
            attempts += 1
            try:
                response = self.generate(
                    prompt=current_prompt,
                    system_prompt=effective_system,
                    temperature=temperature,
                    format_json=True,
                    image_b64=image_b64,
                )
            except TypeError:
                try:
                    response = self.generate(
                        prompt=current_prompt,
                        system_prompt=effective_system,
                        temperature=temperature,
                        format_json=True,
                    )
                except TypeError:
                    response = self.generate(
                        prompt=current_prompt,
                        system_prompt=effective_system,
                        temperature=temperature,
                    )

            raw_text = response.content.strip()
            extracted_json = extract_json_string(raw_text)

            try:
                # Validate against Pydantic schema
                return schema.model_validate_json(extracted_json)
            except (json.JSONDecodeError, ValidationError) as exc:
                if attempts > max_retries:
                    raise AIStructuredOutputError(
                        message=f"Model output failed schema validation: {exc}",
                        raw_output=raw_text,
                        provider=self.name,
                        suggestion=(
                            "The model did not return JSON matching the schema. "
                            "Consider using a larger model or adjusting the prompt."
                        ),
                    ) from exc

                # Prepare retry prompt with specific error feedback
                current_prompt = (
                    f"{prompt}\n\n"
                    f"[CORRECTION REQUIRED]\n"
                    f"Your previous response produced this validation error:\n{exc}\n"
                    f"Raw response was:\n{raw_text}\n\n"
                    "Please regenerate the JSON object strictly matching the schema without any markdown formatting."
                )

        raise AIStructuredOutputError(
            message="Exceeded maximum retries for structured output validation.",
            raw_output="",
            provider=self.name,
        )


def mask_api_key(key: Optional[str]) -> str:
    """Safely mask an API key for logs and UI display."""
    if not key or not key.strip():
        return "(none)"
    k = key.strip()
    if len(k) <= 8:
        return "********"
    return f"{k[:3]}...{k[-4:]}"

