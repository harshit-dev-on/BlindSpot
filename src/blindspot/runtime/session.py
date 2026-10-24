"""Data models for runtime browser sessions and inspection findings."""

from typing import List, Optional
from pydantic import BaseModel, Field


class ViewportSize(BaseModel):
    """Browser viewport dimensions."""

    width: int
    height: int


class BoundingBox(BaseModel):
    """Element coordinates and dimensions on the rendered page."""

    x: int
    y: int
    width: int
    height: int


class InteractiveElement(BaseModel):
    """Discovered interactive element on the inspected web page."""

    element_type: str = Field(
        ...,
        description="Category: 'button', 'link', 'input', 'select', 'textarea', or 'interactive'",
    )
    tag: str = Field(..., description="HTML tag name in lowercase (e.g., 'button', 'a', 'input')")
    text: str = Field(default="", description="Visible text content or value")
    aria_label: str = Field(default="", description="Accessibility label from aria-label")
    name: str = Field(default="", description="Element name attribute")
    id: str = Field(default="", description="Element id attribute")
    placeholder: str = Field(default="", description="Input placeholder text")
    input_type: str = Field(default="", description="Input type (e.g., 'text', 'submit')")
    href: str = Field(default="", description="Target link URL for anchor elements")
    bounding_box: Optional[BoundingBox] = Field(
        default=None, description="Coordinates and size of visible element"
    )


class InspectionSummary(BaseModel):
    """Aggregate statistics for an inspection run."""

    total_interactive_elements: int
    links_count: int
    buttons_count: int
    form_fields_count: int
    text_length: int


class BrowserInspectionResult(BaseModel):
    """Structured inspection findings saved for analysis and persona generation."""

    timestamp: str
    requested_url: str
    final_url: str
    context: str
    title: str
    viewport: ViewportSize
    browser: str
    screenshot_path: str
    result_json_path: str
    summary: InspectionSummary
    interactive_elements: List[InteractiveElement]
    page_text: str
