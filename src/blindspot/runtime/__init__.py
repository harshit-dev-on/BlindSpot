"""Runtime execution engine for BlindSpot (Strix parity).

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

__all__ = [
    "BoundingBox",
    "BrowserInspectionResult",
    "BrowserInspector",
    "InspectionSummary",
    "InteractiveElement",
    "ViewportSize",
    "ensure_browser_engine",
    "inspect_website",
]
