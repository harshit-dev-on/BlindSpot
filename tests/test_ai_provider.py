"""Unit tests for AI providers, JSON extraction, and structured output parsing."""

import json
from unittest.mock import MagicMock, patch
import httpx
from pydantic import BaseModel, Field
import pytest

from blindspot.ai.base import extract_json_string
from blindspot.ai.exceptions import (
    AIAuthenticationError,
    AIConnectionError,
    AIModelNotFoundError,
    AIStructuredOutputError,
    AITimeoutError,
)
from blindspot.ai.factory import create_provider
from blindspot.ai.models import AIResponse
from blindspot.ai.providers.ollama import OllamaProvider
from blindspot.ai.providers.openai_compatible import OpenAICompatibleProvider, mask_api_key
from blindspot.config.models import AIConfig


class SampleUXTask(BaseModel):
    task_name: str
    target_selector: str
    expected_outcome: str


class SamplePersona(BaseModel):
    name: str
    age: int
    tasks: list[SampleUXTask] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# JSON Extraction Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_extract_json_string_clean():
    raw = '{"name": "Alice", "age": 30}'
    assert extract_json_string(raw) == raw


def test_extract_json_string_fenced():
    raw = """Here is the result:
```json
{
  "name": "Bob",
  "age": 25
}
```
Hope that helps!"""
    extracted = extract_json_string(raw)
    parsed = json.loads(extracted)
    assert parsed["name"] == "Bob"
    assert parsed["age"] == 25


def test_extract_json_string_with_conversational_text():
    raw = 'Sure, here is your output: {"name": "Charlie", "age": 40} Thanks!'
    extracted = extract_json_string(raw)
    parsed = json.loads(extracted)
    assert parsed["name"] == "Charlie"


# ─────────────────────────────────────────────────────────────────────────────
# Ollama Provider Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_ollama_health_success():
    provider = OllamaProvider(model="gemma4", base_url="http://localhost:11434")

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "models": [{"name": "gemma4:latest"}, {"name": "llama3:latest"}]
    }

    with patch.object(httpx.Client, "get", return_value=mock_response):
        status = provider.check_health()
        assert status.is_reachable is True
        assert status.model_available is True
        assert "gemma4" in status.message


def test_ollama_health_model_missing():
    provider = OllamaProvider(model="mistral", base_url="http://localhost:11434")

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "models": [{"name": "gemma4:latest"}]
    }

    with patch.object(httpx.Client, "get", return_value=mock_response):
        status = provider.check_health()
        assert status.is_reachable is True
        assert status.model_available is False
        assert "ollama pull mistral" in status.message


def test_ollama_health_connection_error():
    provider = OllamaProvider(model="gemma4", base_url="http://localhost:11434")

    with patch.object(httpx.Client, "get", side_effect=httpx.ConnectError("Connection refused")):
        status = provider.check_health()
        assert status.is_reachable is False
        assert status.model_available is False
        assert "ollama serve" in status.message


def test_ollama_generate_success():
    provider = OllamaProvider(model="gemma4")

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "message": {"content": "Hello from Gemma 4!"},
        "prompt_eval_count": 10,
        "eval_count": 5,
        "total_duration": 150000000,
    }

    with patch.object(httpx.Client, "post", return_value=mock_response):
        res = provider.generate("Hello")
        assert isinstance(res, AIResponse)
        assert res.content == "Hello from Gemma 4!"
        assert res.model == "gemma4"
        assert res.provider == "ollama"


def test_ollama_generate_model_not_found():
    provider = OllamaProvider(model="nonexistent")

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 404
    mock_response.text = "model nonexistent not found"

    with patch.object(httpx.Client, "post", return_value=mock_response):
        with pytest.raises(AIModelNotFoundError, match="ollama pull nonexistent"):
            provider.generate("Hello")


def test_ollama_generate_timeout():
    provider = OllamaProvider(model="gemma4")

    with patch.object(httpx.Client, "post", side_effect=httpx.TimeoutException("Timed out")):
        with pytest.raises(AITimeoutError, match="timed out"):
            provider.generate("Hello")


def test_ollama_generate_structured_success():
    provider = OllamaProvider(model="gemma4")

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "message": {
            "content": json.dumps({
                "name": "Sarah Developer",
                "age": 32,
                "tasks": [
                    {"task_name": "Find docs", "target_selector": "a.nav-docs", "expected_outcome": "Docs open"}
                ]
            })
        }
    }

    with patch.object(httpx.Client, "post", return_value=mock_response):
        result = provider.generate_structured("Generate a persona", schema=SamplePersona)
        assert isinstance(result, SamplePersona)
        assert result.name == "Sarah Developer"
        assert result.age == 32
        assert len(result.tasks) == 1


def test_ollama_generate_structured_retry_on_bad_json():
    provider = OllamaProvider(model="gemma4")

    # First attempt: invalid JSON string. Second attempt: valid JSON
    bad_resp = MagicMock(spec=httpx.Response)
    bad_resp.status_code = 200
    bad_resp.json.return_value = {"message": {"content": "Not valid json at all"}}

    good_resp = MagicMock(spec=httpx.Response)
    good_resp.status_code = 200
    good_resp.json.return_value = {
        "message": {"content": json.dumps({"name": "Recovered Persona", "age": 28, "tasks": []})}
    }

    with patch.object(httpx.Client, "post", side_effect=[bad_resp, good_resp]):
        result = provider.generate_structured("Generate a persona", schema=SamplePersona, max_retries=1)
        assert result.name == "Recovered Persona"


# ─────────────────────────────────────────────────────────────────────────────
# OpenAI-Compatible Provider Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_mask_api_key():
    assert mask_api_key(None) == "(none)"
    assert mask_api_key("") == "(none)"
    assert mask_api_key("short") == "********"
    assert mask_api_key("sk-proj-1234567890abcdef") == "sk-...cdef"


def test_openai_compatible_reads_env_key(monkeypatch):
    monkeypatch.setenv("TEST_AI_KEY", "sk-secret-test-key-123456")
    provider = OpenAICompatibleProvider(
        model="gpt-4o-mini",
        api_key_env="TEST_AI_KEY",
    )
    assert provider._api_key == "sk-secret-test-key-123456"
    assert "sk-...3456" in provider.masked_api_key


def test_openai_compatible_health_check_401():
    provider = OpenAICompatibleProvider(model="gpt-4o-mini", api_key="invalid-key")

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 401

    with patch.object(httpx.Client, "get", return_value=mock_response):
        status = provider.check_health()
        assert status.is_reachable is True
        assert status.model_available is False
        assert "Authentication failed" in status.message


def test_openai_compatible_generate_success():
    provider = OpenAICompatibleProvider(model="gpt-4o-mini", api_key="sk-test-key")

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "model": "gpt-4o-mini",
        "choices": [{"message": {"content": "Hello from OpenAI-compatible endpoint"}}],
        "usage": {"total_tokens": 15},
    }

    with patch.object(httpx.Client, "post", return_value=mock_response):
        res = provider.generate("Say hello")
        assert res.content == "Hello from OpenAI-compatible endpoint"
        assert res.provider == "openai_compatible"
        assert res.model == "gpt-4o-mini"


def test_openai_compatible_fallback_for_response_format():
    provider = OpenAICompatibleProvider(model="custom-model", api_key="sk-test")

    # When format_json is requested, custom endpoint might return 400 for response_format
    fail_response = MagicMock(spec=httpx.Response)
    fail_response.status_code = 400
    fail_response.text = "Unrecognized request argument supplied: response_format"

    success_response = MagicMock(spec=httpx.Response)
    success_response.status_code = 200
    success_response.json.return_value = {
        "model": "custom-model",
        "choices": [{"message": {"content": '{"name": "Fallback User", "age": 22, "tasks": []}'}}],
    }

    with patch.object(httpx.Client, "post", side_effect=[fail_response, success_response]):
        res = provider.generate_structured("Return user", schema=SamplePersona)
        assert res.name == "Fallback User"


def test_factory_creation():
    ollama_cfg = AIConfig(provider="ollama", model="gemma4")
    p1 = create_provider(ollama_cfg)
    assert isinstance(p1, OllamaProvider)

    openai_cfg = AIConfig(provider="openai_compatible", model="gpt-4o")
    p2 = create_provider(openai_cfg)
    assert isinstance(p2, OpenAICompatibleProvider)
