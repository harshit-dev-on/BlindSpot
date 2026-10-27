"""Runtime execution engine for BlindSpot.

Manages browser automation, environment provisioning, and page inspection.
"""

from blindspot.runtime.browser import (
    BrowserInspector,
    inspect_website,
)
from blindspot.runtime.provisioning import ensure_browser_engine
from blindspot.runtime.session import (
    BoundingBox,
    BrowserInspectionResult,
    InspectionSummary,
    InteractiveElement,
    ViewportSize,
)

from blindspot.runtime.scroll_test import run_live_scroll_test

__all__ = [
    "BoundingBox",
    "BrowserInspectionResult",
    "BrowserInspector",
    "InspectionSummary",
    "InteractiveElement",
    "ViewportSize",
    "ensure_browser_engine",
    "inspect_website",
    "run_live_scroll_test",
]
