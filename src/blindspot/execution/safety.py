"""Safety policies, URL restrictions, private network defenses, and destructive action guards."""

import ipaddress
import re
from typing import Optional, Set, Tuple
from urllib.parse import urlsplit


BLOCKED_HOSTNAMES: Set[str] = {
    "localhost",
    "metadata.google.internal",
    "instance-data",
}

BLOCKED_DOMAINS_SUFFIXES: Tuple[str, ...] = (
    ".local",
    ".internal",
    ".localhost",
)

DESTRUCTIVE_TEXT_PATTERNS: Tuple[re.Pattern, ...] = (
    re.compile(r"\b(place\s+(?:\w+\s+)?order|buy\s+now|pay\s+now|confirm\s+(?:\w+\s+)?payment|complete\s+(?:\w+\s+)?order|charge\s+card)\b", re.IGNORECASE),
    re.compile(r"\b(delete\s+(?:\w+\s+)?account|terminate\s+(?:\w+\s+)?account|wipe\s+data|cancel\s+subscription)\b", re.IGNORECASE),
)

SENSITIVE_FIELD_PATTERNS: Tuple[re.Pattern, ...] = (
    re.compile(r"(password|passwd|pwd|cvv|cvc|creditcard|cardnumber|ssn|secret|apikey|token)", re.IGNORECASE),
)


def is_ip_private_or_restricted(host: str, allow_loopback: bool = False) -> bool:
    """Check if a hostname or IP address resolves to a loopback, private, or link-local range."""
    # Strip brackets if IPv6
    clean_host = host.strip("[]")

    try:
        ip = ipaddress.ip_address(clean_host)
        if allow_loopback and ip.is_loopback:
            return False
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        # Not a raw IP address; check hostname
        return False


def validate_navigation_url(
    url: str,
    allowed_domains: Optional[Set[str]] = None,
    allow_external_http: bool = True,
    allow_local: bool = False,
) -> Tuple[bool, Optional[str]]:
    """Validate that a target URL is safe to visit.

    Enforces:
    - Only HTTP and HTTPS schemes.
    - No localhost, private IP ranges (10.x, 192.168.x, 172.16.x), or link-local/cloud metadata.
    - Allowed domain restrictions if specified.
    - If allow_local=True, permits loopback (localhost, 127.0.0.1, ::1) while keeping
      cloud metadata and private subnets strictly blocked.

    Returns:
        (is_safe, error_reason)
    """
    if not url or not url.strip():
        return False, "URL cannot be empty."

    try:
        parts = urlsplit(url.strip())
    except Exception as exc:
        return False, f"Malformed URL: {exc}"

    # 1. Scheme check
    scheme = parts.scheme.lower()
    if scheme not in ("http", "https"):
        return False, f"Forbidden URL scheme '{scheme}'. Only HTTP and HTTPS are permitted."

    # 2. Hostname check
    host = (parts.hostname or "").lower().strip()
    if not host:
        return False, "URL must include a valid hostname."

    # Cloud metadata is unconditionally blocked
    if host in ("metadata.google.internal", "instance-data"):
        return False, f"Access to cloud metadata '{host}' is strictly blocked."

    if host == "localhost":
        if not allow_local:
            return False, f"Access to '{host}' is blocked for security (use --allow-local for local testing)."
    elif host in BLOCKED_HOSTNAMES:
        return False, f"Access to '{host}' is blocked for security."

    for suffix in BLOCKED_DOMAINS_SUFFIXES:
        if host.endswith(suffix):
            if suffix == ".localhost" and allow_local:
                continue
            return False, f"Access to local/internal domains ('{host}') is forbidden."

    # 3. IP range checks (Cloud metadata 169.254.169.254, RFC 1918 private IPs, loopback)
    if is_ip_private_or_restricted(host, allow_loopback=allow_local):
        return False, f"Access to private or link-local IP '{host}' is strictly blocked."

    # 4. Optional domain whitelist check
    if allowed_domains and not allow_external_http:
        # Normalize and match host against allowed domain roots
        domain_matched = False
        for allowed in allowed_domains:
            norm_allowed = allowed.lower().lstrip("www.").strip()
            norm_host = host.lstrip("www.")
            if norm_host == norm_allowed or norm_host.endswith(f".{norm_allowed}"):
                domain_matched = True
                break
        if not domain_matched:
            return False, f"Navigation to '{host}' is outside the allowed test scope."

    return True, None


def is_action_destructive(target: Optional[str], value: Optional[str]) -> Tuple[bool, Optional[str]]:
    """Inspect element identifier and value to prevent accidental real purchases or deletions."""
    combined_text = f"{target or ''} {value or ''}"

    for pattern in DESTRUCTIVE_TEXT_PATTERNS:
        match = pattern.search(combined_text)
        if match:
            return True, f"Blocked potentially destructive action matching '{match.group(0)}'."

    return False, None


def mask_sensitive_input(target: Optional[str], value: Optional[str]) -> Optional[str]:
    """Mask passwords or sensitive values from being stored in logs or records."""
    if not value:
        return value

    target_str = (target or "").lower()
    for pattern in SENSITIVE_FIELD_PATTERNS:
        if pattern.search(target_str):
            return "********"

    return value
