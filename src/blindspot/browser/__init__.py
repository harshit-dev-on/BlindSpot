"""Browser inspection module for BlindSpot using Playwright."""

from blindspot.runtime import (
    BoundingBox,
    BrowserInspectionResult,
    BrowserInspector,
    InspectionSummary,
    InteractiveElement,
    ViewportSize,
    ensure_browser_engine,
    inspect_website,
)
from blindspot.runtime.browser import EXTRACT_INTERACTIVE_ELEMENTS_JS, EXTRACT_PAGE_TEXT_JS

__all__ = [
    "BoundingBox",
    "BrowserInspectionResult",
    "BrowserInspector",
    "InspectionSummary",
    "InteractiveElement",
    "ViewportSize",
    "ensure_browser_engine",
    "inspect_website",
    "EXTRACT_INTERACTIVE_ELEMENTS_JS",
    "EXTRACT_PAGE_TEXT_JS",
]
