"""Automated unit and integration tests for the Playwright browser inspector."""

from pathlib import Path
import pytest
from blindspot.browser import BrowserInspector, BrowserInspectionResult, inspect_website


def test_browser_inspector_defaults():
    """Verify default configurations of BrowserInspector."""
    inspector = BrowserInspector()
    assert inspector.browser_type == "chromium"
    assert inspector.headless is True
    assert inspector.viewport_width == 1280
    assert inspector.viewport_height == 800


def test_browser_inspector_invalid_browser():
    """Verify error raised when invalid browser is configured."""
    with pytest.raises(ValueError, match="Unsupported browser 'opera'"):
        BrowserInspector(browser_type="opera")


def test_browser_inspector_custom_directory(tmp_path: Path):
    """Verify custom directory is created and used for artifacts."""
    inspector = BrowserInspector()
    custom_dir = tmp_path / "custom_inspection_dir"
    res_dir = inspector._create_run_directory(
        url="https://example.com", base_output_dir=custom_dir
    )
    assert res_dir == custom_dir
    assert custom_dir.exists()


def test_browser_inspector_default_run_directory():
    """Verify default unique directory structure."""
    inspector = BrowserInspector()
    res_dir = inspector._create_run_directory(url="https://example.com/test")
    assert "reports" in str(res_dir)
    assert "run_example_com_" in res_dir.name
    assert res_dir.exists()


def test_browser_inspection_with_local_html(tmp_path: Path):
    """Test full browser inspection workflow using an HTML page."""
    html_content = """<!DOCTYPE html>
<html>
<head><title>Test UX Page</title></head>
<body>
    <h1>Welcome to the Test Page</h1>
    <p>This is a test description paragraph with useful text.</p>
    <a href="https://example.com/about">About Us</a>
    <a href="https://example.com/docs">Documentation</a>
    <button type="button" id="cta-btn">Click Me</button>
    <form>
        <label for="email">Email</label>
        <input type="email" id="email" name="user_email" placeholder="you@domain.com" />
        <textarea name="feedback" placeholder="Your feedback"></textarea>
    </form>
</body>
</html>
"""
    html_file = tmp_path / "page.html"
    html_file.write_text(html_content, encoding="utf-8")

    file_url = html_file.as_uri()
    output_dir = tmp_path / "artifacts"

    result = inspect_website(
        url=file_url,
        context="Testing local HTML inspection workflow",
        output_dir=output_dir,
        browser_type="chromium",
        headless=True,
    )

    assert isinstance(result, BrowserInspectionResult)
    assert result.title == "Test UX Page"
    assert "Welcome to the Test Page" in result.page_text
    assert result.summary.links_count == 2
    assert result.summary.buttons_count == 1
    assert result.summary.form_fields_count == 2
    assert result.summary.total_interactive_elements == 5

    # Check generated artifacts
    assert Path(result.screenshot_path).exists()
    assert Path(result.result_json_path).exists()
    assert Path(result.screenshot_path).stat().st_size > 0
    assert Path(result.result_json_path).stat().st_size > 0
