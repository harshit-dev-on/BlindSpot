"""Unit tests for URL and context validation logic."""

from blindspot.core.validation import validate_context, validate_url


def test_validate_url_valid_https():
    result = validate_url("https://example.com")
    assert result.is_valid is True
    assert result.error_message is None


def test_validate_url_valid_http():
    result = validate_url("http://sub.domain.org/app?page=1#top")
    assert result.is_valid is True
    assert result.error_message is None


def test_validate_url_valid_localhost():
    result = validate_url("http://localhost:3000/dashboard")
    assert result.is_valid is True
    assert result.error_message is None


def test_validate_url_valid_ip():
    result = validate_url("http://127.0.0.1:8080")
    assert result.is_valid is True
    assert result.error_message is None


def test_validate_url_empty():
    result = validate_url("")
    assert result.is_valid is False
    assert "empty" in result.error_message.lower()
    assert result.suggestion is not None


def test_validate_url_missing_scheme():
    result = validate_url("example.com")
    assert result.is_valid is False
    assert "protocol scheme" in result.error_message.lower()
    assert "https://example.com" in result.suggestion


def test_validate_url_unsupported_scheme():
    result = validate_url("ftp://ftp.example.com/file")
    assert result.is_valid is False
    assert "unsupported" in result.error_message.lower()


def test_validate_url_with_spaces():
    result = validate_url("https://exa mple.com")
    assert result.is_valid is False
    assert "spaces" in result.error_message.lower()


def test_validate_url_missing_host():
    result = validate_url("https://")
    assert result.is_valid is False
    assert "missing a host" in result.error_message.lower()


def test_validate_url_invalid_domain_structure():
    result = validate_url("https://justaword")
    assert result.is_valid is False
    assert "domain or local host" in result.error_message.lower()


def test_validate_context_valid():
    res, cleaned = validate_context("An e-commerce store selling handcrafted ceramic mugs.")
    assert res.is_valid is True
    assert "handcrafted" in cleaned


def test_validate_context_empty():
    res, _ = validate_context("")
    assert res.is_valid is False
    assert "empty" in res.error_message.lower()
    assert res.suggestion is not None


def test_validate_context_too_short():
    res, _ = validate_context("Hi there")
    assert res.is_valid is False
    assert "too brief" in res.error_message.lower()


def test_validate_context_from_file(tmp_path):
    context_file = tmp_path / "context.txt"
    context_file.write_text("Context loaded from temporary file for testing purposes.", encoding="utf-8")

    res, cleaned = validate_context(f"@{context_file}")
    assert res.is_valid is True
    assert "Context loaded from temporary file" in cleaned


def test_validate_context_missing_file():
    res, _ = validate_context("@non_existent_file_12345.txt")
    assert res.is_valid is False
    assert "not found" in res.error_message.lower()
