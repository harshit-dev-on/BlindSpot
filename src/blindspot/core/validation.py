"""Input validation logic for website URLs and contextual descriptions."""

import os
from urllib.parse import urlsplit
from typing import Tuple
from blindspot.core.models import ValidationResult


SUPPORTED_SCHEMES = ("http", "https")
MIN_CONTEXT_LENGTH = 10
MAX_CONTEXT_LENGTH = 50_000


def validate_url(url: str) -> ValidationResult:
    """Validate a target website URL for UX testing.

    Ensures the URL is non-empty, specifies an http/https scheme,
    and has a valid network location (hostname/domain or localhost).

    Args:
        url: The input URL string.

    Returns:
        ValidationResult indicating whether the URL is valid, with actionable errors and suggestions.
    """
    if not url or not url.strip():
        return ValidationResult(
            is_valid=False,
            error_message="The website URL cannot be empty.",
            suggestion="Specify a URL using --url (e.g., --url https://example.com).",
        )

    cleaned_url = url.strip()

    if " " in cleaned_url:
        return ValidationResult(
            is_valid=False,
            error_message="The URL contains spaces.",
            suggestion="Remove any spaces from the URL (e.g., https://example.com).",
        )

    try:
        parsed = urlsplit(cleaned_url)
    except Exception as exc:
        return ValidationResult(
            is_valid=False,
            error_message=f"Failed to parse URL: {exc}",
            suggestion="Check that the URL is properly formatted (e.g., https://example.com).",
        )

    # Check scheme
    if not parsed.scheme:
        return ValidationResult(
            is_valid=False,
            error_message="URL is missing a protocol scheme (http:// or https://).",
            suggestion=f"Did you mean 'https://{cleaned_url}'? BlindSpot requires an explicit 'https://' or 'http://' prefix.",
        )

    if parsed.scheme.lower() not in SUPPORTED_SCHEMES:
        return ValidationResult(
            is_valid=False,
            error_message=f"Unsupported URL scheme '{parsed.scheme}'.",
            suggestion=f"BlindSpot only inspects web applications via HTTP or HTTPS. Please use https:// or http://.",
        )

    # Check hostname / netloc
    netloc = parsed.netloc.strip()
    if not netloc:
        return ValidationResult(
            is_valid=False,
            error_message="URL is missing a host or domain name.",
            suggestion="Provide a valid domain or local server address (e.g., https://example.com or http://localhost:3000).",
        )

    hostname = parsed.hostname
    if not hostname:
        return ValidationResult(
            is_valid=False,
            error_message="Could not extract a valid host name from the URL.",
            suggestion="Ensure the domain format is correct (e.g., https://example.com).",
        )

    # Check for minimal domain structure (has dot or is localhost/ip)
    is_localhost = hostname.lower() in ("localhost", "127.0.0.1", "::1", "0.0.0.0")
    if not is_localhost and "." not in hostname:
        return ValidationResult(
            is_valid=False,
            error_message=f"Host '{hostname}' does not appear to be a valid domain or local host.",
            suggestion="Ensure the host has a valid domain extension (e.g., example.com) or use 'localhost'.",
        )

    return ValidationResult(is_valid=True)


def validate_context(context: str) -> Tuple[ValidationResult, str]:
    """Validate the website purpose and audience context description.

    Supports direct text input as well as file references (e.g., passing a path or @context.txt).

    Args:
        context: Context string or file path reference.

    Returns:
        A tuple of (ValidationResult, resolved_context_text).
    """
    if not context or not context.strip():
        return (
            ValidationResult(
                is_valid=False,
                error_message="Context description cannot be empty.",
                suggestion="Provide a description of the website purpose and audience (e.g., --context \"An online bookstore for technical software developers\").",
            ),
            "",
        )

    cleaned_context = context.strip()

    # Check if context references a file (e.g., @context.txt or existing file path)
    file_path = None
    if cleaned_context.startswith("@"):
        file_path = cleaned_context[1:].strip()
    elif os.path.isfile(cleaned_context):
        file_path = cleaned_context

    if file_path is not None:
        if not os.path.exists(file_path):
            return (
                ValidationResult(
                    is_valid=False,
                    error_message=f"Context file '{file_path}' was not found.",
                    suggestion="Check that the file path is correct or pass the context string directly enclosed in quotes.",
                ),
                "",
            )
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                cleaned_context = f.read().strip()
        except Exception as exc:
            return (
                ValidationResult(
                    is_valid=False,
                    error_message=f"Could not read context file '{file_path}': {exc}",
                    suggestion="Ensure the file is readable and encoded in UTF-8.",
                ),
                "",
            )

    if len(cleaned_context) < MIN_CONTEXT_LENGTH:
        return (
            ValidationResult(
                is_valid=False,
                error_message=f"Context description is too brief ({len(cleaned_context)} characters).",
                suggestion=f"Provide more context (at least {MIN_CONTEXT_LENGTH} characters) describing the website's purpose and target audience.",
            ),
            "",
        )

    if len(cleaned_context) > MAX_CONTEXT_LENGTH:
        return (
            ValidationResult(
                is_valid=False,
                error_message=f"Context description exceeds maximum supported length ({len(cleaned_context)} / {MAX_CONTEXT_LENGTH} characters).",
                suggestion="Shorten the context description or provide a summary of the website's key features and target users.",
            ),
            "",
        )

    return (ValidationResult(is_valid=True), cleaned_context)
