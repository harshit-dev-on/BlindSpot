"""Browser inspection module for BlindSpot using Playwright."""

from blindspot.browser.models import (
    BoundingBox,
    BrowserInspectionResult,
    InspectionSummary,
    InteractiveElement,
    ViewportSize,
)
from blindspot.browser.inspector import BrowserInspector, inspect_website

__all__ = [
    "BoundingBox",
    "BrowserInspectionResult",
    "BrowserInspector",
    "InspectionSummary",
    "InteractiveElement",
    "ViewportSize",
    "inspect_website",
]
