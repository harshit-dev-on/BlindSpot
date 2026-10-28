"""Core Playwright browser inspection engine for BlindSpot runtime."""

from datetime import datetime, timezone
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlsplit

from playwright.sync_api import Error as PlaywrightError, sync_playwright

from blindspot.runtime.provisioning import ensure_browser_engine
from blindspot.runtime.session import (
    BoundingBox,
    BrowserInspectionResult,
    InspectionSummary,
    InteractiveElement,
    ViewportSize,
)

# JavaScript snippet to extract visible interactive elements in a single round-trip
EXTRACT_INTERACTIVE_ELEMENTS_JS = """
() => {
    const isVisible = (el) => {
        if (!el) return false;
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
    };

    const candidates = document.querySelectorAll(
        'button, a[href], input, select, textarea, [role="button"], [role="link"], [tabindex="0"]'
    );
    const elements = [];

    for (const el of candidates) {
        if (!isVisible(el)) continue;
        if (el.id.startsWith('__blindspot') || el.closest('[id^="__blindspot"]')) continue;
        const rect = el.getBoundingClientRect();
        const tag = el.tagName.toLowerCase();

        let elType = 'interactive';
        if (tag === 'a') {
            elType = 'link';
        } else if (tag === 'button' || el.getAttribute('role') === 'button') {
            elType = 'button';
        } else if (tag === 'input') {
            const inputType = (el.getAttribute('type') || 'text').toLowerCase();
            if (['button', 'submit', 'reset'].includes(inputType)) {
                elType = 'button';
            } else {
                elType = 'input';
            }
        } else if (tag === 'select') {
            elType = 'select';
        } else if (tag === 'textarea') {
            elType = 'textarea';
        }

        const rawText = el.innerText || el.textContent || (el.value ? String(el.value) : '') || '';
        const text = rawText.replace(/\\s+/g, ' ').trim().slice(0, 150);
        const ariaLabel = (el.getAttribute('aria-label') || '').trim();
        const name = (el.getAttribute('name') || '').trim();
        const id = (el.id || '').trim();
        const placeholder = (el.getAttribute('placeholder') || '').trim();
        const inputType = (el.getAttribute('type') || '').trim();
        const href = (el.getAttribute('href') || '').trim().slice(0, 300);

        elements.push({
            element_type: elType,
            tag: tag,
            text: text,
            aria_label: ariaLabel,
            name: name,
            id: id,
            placeholder: placeholder,
            input_type: inputType,
            href: href,
            bounding_box: {
                x: Math.round(rect.x),
                y: Math.round(rect.y),
                width: Math.round(rect.width),
                height: Math.round(rect.height)
            }
        });
    }
    return elements;
}
"""

EXTRACT_DOM_SNAPSHOT_JS = """
() => {
    const isVisible = (el) => {
        if (!el) return false;
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden' || parseFloat(style.opacity || '1') < 0.05) return false;
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
    };

    const selector = 'button, a[href], input, select, textarea, [role="button"], [role="link"], [role="tab"], [role="menuitem"], [role="checkbox"], [role="switch"], [role="option"], [tabindex="0"]';
    const candidates = Array.from(document.querySelectorAll(selector));
    const elements = [];
    let idx = 1;

    for (const el of candidates) {
        if (!isVisible(el)) continue;
        if (el.id.startsWith('__blindspot') || el.closest('[id^="__blindspot"]')) continue;

        const rect = el.getBoundingClientRect();
        const tag = el.tagName.toLowerCase();
        const style = window.getComputedStyle(el);

        let elType = 'interactive';
        if (tag === 'a') elType = 'link';
        else if (tag === 'button' || el.getAttribute('role') === 'button') elType = 'button';
        else if (tag === 'input') {
            const inputType = (el.getAttribute('type') || 'text').toLowerCase();
            elType = ['button', 'submit', 'reset'].includes(inputType) ? 'button' : 'input';
        } else if (tag === 'select') elType = 'select';
        else if (tag === 'textarea') elType = 'textarea';

        const rawText = el.innerText || el.textContent || (el.value ? String(el.value) : '') || '';
        const text = rawText.replace(/\\s+/g, ' ').trim().slice(0, 100);
        const ariaLabel = (el.getAttribute('aria-label') || '').trim().slice(0, 80);
        const placeholder = (el.getAttribute('placeholder') || '').trim().slice(0, 60);
        const idVal = (el.id || '').trim();
        const nameVal = (el.getAttribute('name') || '').trim();
        const hrefVal = (el.getAttribute('href') || '').trim().slice(0, 120);
        const inputType = (el.getAttribute('type') || '').trim();
        const disabled = el.disabled || el.getAttribute('aria-disabled') === 'true';

        // Extract key CSS styling attributes that influence UX
        const cssProps = [];
        if (style.color) cssProps.push(`color: ${style.color}`);
        if (style.backgroundColor && style.backgroundColor !== 'rgba(0, 0, 0, 0)' && style.backgroundColor !== 'transparent') {
            cssProps.push(`bg: ${style.backgroundColor}`);
        }
        if (style.fontSize) cssProps.push(`font: ${style.fontSize}`);
        if (style.cursor && style.cursor !== 'auto') cssProps.push(`cursor: ${style.cursor}`);
        if (style.display && style.display !== 'block' && style.display !== 'inline') cssProps.push(`display: ${style.display}`);

        const cssSummary = cssProps.join('; ');

        elements.push({
            ref: `@e${idx}`,
            index: idx,
            element_type: elType,
            tag: tag,
            id: idVal,
            name: nameVal,
            text: text,
            aria_label: ariaLabel,
            placeholder: placeholder,
            input_type: inputType,
            href: hrefVal,
            disabled: disabled,
            css: cssSummary,
            bounding_box: {
                x: Math.round(rect.x),
                y: Math.round(rect.y),
                width: Math.round(rect.width),
                height: Math.round(rect.height)
            }
        });
        idx++;
    }

    // Prioritize elements visible in or near current viewport, cap at 60 to prevent token bloat
    const vh = window.innerHeight || 800;
    elements.sort((a, b) => {
        const aInView = a.bounding_box.y >= -100 && a.bounding_box.y <= vh + 100;
        const bInView = b.bounding_box.y >= -100 && b.bounding_box.y <= vh + 100;
        if (aInView && !bInView) return -1;
        if (!aInView && bInView) return 1;
        return a.bounding_box.y - b.bounding_box.y;
    });

    const cappedElements = elements.slice(0, 60);
    cappedElements.forEach((el, i) => {
        el.index = i + 1;
        el.ref = `@e${i + 1}`;
    });

    // Extract semantic DOM HTML snippet (cleaned of scripts, styles, SVGs)
    const clone = document.body.cloneNode(true);
    const toRemove = clone.querySelectorAll('script, style, noscript, svg, iframe, canvas, link, meta, [id^="__blindspot"]');
    toRemove.forEach(n => n.remove());

    const allNodes = clone.querySelectorAll('*');
    allNodes.forEach(node => {
        const keepAttrs = ['id', 'class', 'role', 'type', 'name', 'href', 'placeholder', 'aria-label', 'aria-expanded', 'disabled', 'value', 'title'];
        const attrs = Array.from(node.attributes);
        for (const attr of attrs) {
            if (!keepAttrs.includes(attr.name.toLowerCase())) {
                node.removeAttribute(attr.name);
            }
        }
    });

    let domHtml = clone.innerHTML || '';
    domHtml = domHtml.replace(/\\s+/g, ' ').replace(/> </g, '><').trim().slice(0, 3500);

    return {
        elements: cappedElements,
        dom_html: domHtml,
    };
}
"""

EXTRACT_PAGE_TEXT_JS = """
() => {
    const body = document.body;
    if (!body) return '';
    return body.innerText ? body.innerText.trim() : '';
}
"""


class BrowserInspector:
    """Manages browser sessions and website inspection using Playwright."""

    def __init__(
        self,
        browser_type: str = "chromium",
        headless: bool = True,
        viewport_width: int = 1280,
        viewport_height: int = 800,
        timeout_ms: int = 30000,
        allow_local: bool = False,
    ) -> None:
        self.browser_type = browser_type.lower()
        self.headless = headless
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.timeout_ms = timeout_ms
        self.allow_local = allow_local

        valid_browsers = ("chromium", "firefox", "webkit")
        if self.browser_type not in valid_browsers:
            raise ValueError(
                f"Unsupported browser '{self.browser_type}'. Supported browsers: {', '.join(valid_browsers)}"
            )

    def _create_run_directory(
        self, url: str, base_output_dir: Optional[Union[str, Path]] = None
    ) -> Path:
        """Create a dedicated, unique directory for the current inspection run."""
        if base_output_dir is not None:
            target_dir = Path(base_output_dir)
            target_dir.mkdir(parents=True, exist_ok=True)
            return target_dir

        # Default unique directory under blindspot_reports/, reports/, or BLINDSPOT_REPORTS_DIR
        reports_dir = Path(os.environ.get("BLINDSPOT_REPORTS_DIR", "blindspot_reports" if Path("blindspot_reports").is_dir() else "reports"))
        host = urlsplit(url).netloc or "page"
        clean_host = re.sub(r"[^a-zA-Z0-9]+", "_", host).strip("_")
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = reports_dir / f"run_{clean_host}_{timestamp_str}"
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def inspect(
        self,
        url: str,
        context: str,
        output_dir: Optional[Union[str, Path]] = None,
    ) -> BrowserInspectionResult:
        """Launch browser, load the target URL, collect page data, and capture artifacts.

        Args:
            url: Validated target website URL.
            context: Validated website purpose and target audience description.
            output_dir: Optional custom directory to store inspection artifacts.

        Returns:
            BrowserInspectionResult with structured page observations and artifact paths.
        """
        run_dir = self._create_run_directory(url=url, base_output_dir=output_dir)

        try:
            with sync_playwright() as p:
                browser_launcher = getattr(p, self.browser_type, None)
                if browser_launcher is None:
                    raise ValueError(f"Browser engine '{self.browser_type}' is not supported.")

                try:
                    browser = browser_launcher.launch(headless=self.headless)
                except PlaywrightError as exc:
                    err_msg = str(exc)
                    if "Executable doesn't exist" in err_msg or "Please run" in err_msg:
                        ensure_browser_engine(self.browser_type)
                        browser = browser_launcher.launch(headless=self.headless)
                    else:
                        raise

                try:
                    context_obj = browser.new_context(
                        viewport={
                            "width": self.viewport_width,
                            "height": self.viewport_height,
                        }
                    )
                    page = context_obj.new_page()

                    # Enforce SSRF & URL safety check
                    from blindspot.execution.safety import validate_navigation_url
                    if url.startswith(("http://", "https://")):
                        is_safe, reason = validate_navigation_url(url, allow_local=self.allow_local)
                        if not is_safe:
                            raise ValueError(f"Security Policy Blocked: {reason}")
                    elif not url.startswith("file://") and not self.allow_local:
                        raise ValueError("Forbidden URL scheme. Only HTTP and HTTPS are permitted.")

                    # Reliable loading strategy:
                    page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)

                    # Check for redirect to blocked destination
                    if page.url.startswith(("http://", "https://")):
                        is_safe, reason = validate_navigation_url(page.url, allow_local=self.allow_local)
                        if not is_safe:
                            raise ValueError(f"Redirect blocked by Security Policy: {reason}")

                    try:
                        page.wait_for_load_state("load", timeout=5000)
                    except Exception:
                        pass

                    page.wait_for_timeout(500)

                    # Extract metadata and dimensions
                    final_url = page.url
                    page_title = page.title()
                    vp_size = page.viewport_size or {
                        "width": self.viewport_width,
                        "height": self.viewport_height,
                    }
                    viewport = ViewportSize(
                        width=vp_size.get("width", self.viewport_width),
                        height=vp_size.get("height", self.viewport_height),
                    )

                    # Extract page text content
                    page_text = page.evaluate(EXTRACT_PAGE_TEXT_JS) or ""

                    # Extract visible interactive elements
                    raw_elements: List[Dict[str, Any]] = (
                        page.evaluate(EXTRACT_INTERACTIVE_ELEMENTS_JS) or []
                    )

                    interactive_elements: List[InteractiveElement] = []
                    links_count = 0
                    buttons_count = 0
                    form_fields_count = 0

                    for raw in raw_elements:
                        bbox = None
                        if raw.get("bounding_box"):
                            bbox = BoundingBox(**raw["bounding_box"])

                        elem = InteractiveElement(
                            element_type=raw.get("element_type", "interactive"),
                            tag=raw.get("tag", ""),
                            text=raw.get("text", ""),
                            aria_label=raw.get("aria_label", ""),
                            name=raw.get("name", ""),
                            id=raw.get("id", ""),
                            placeholder=raw.get("placeholder", ""),
                            input_type=raw.get("input_type", ""),
                            href=raw.get("href", ""),
                            bounding_box=bbox,
                        )
                        interactive_elements.append(elem)

                        if elem.element_type == "link":
                            links_count += 1
                        elif elem.element_type == "button":
                            buttons_count += 1
                        elif elem.element_type in ("input", "select", "textarea"):
                            form_fields_count += 1

                    # Capture full-page screenshot
                    screenshot_file = run_dir / "screenshot.png"
                    page.screenshot(path=str(screenshot_file), full_page=True)

                finally:
                    browser.close()

        except PlaywrightError as exc:
            raise RuntimeError(f"Browser navigation failed: {exc}") from exc

        # Assemble summary metrics
        summary = InspectionSummary(
            total_interactive_elements=len(interactive_elements),
            links_count=links_count,
            buttons_count=buttons_count,
            form_fields_count=form_fields_count,
            text_length=len(page_text),
        )

        result_json_file = run_dir / "inspection_result.json"
        now_iso = datetime.now(timezone.utc).isoformat()

        result = BrowserInspectionResult(
            timestamp=now_iso,
            requested_url=url,
            final_url=final_url,
            context=context,
            title=page_title,
            viewport=viewport,
            browser=self.browser_type,
            screenshot_path=str(screenshot_file),
            result_json_path=str(result_json_file),
            summary=summary,
            interactive_elements=interactive_elements,
            page_text=page_text,
        )

        # Write structured JSON artifact
        with open(result_json_file, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))

        return result


def inspect_website(
    url: str,
    context: str,
    output_dir: Optional[Union[str, Path]] = None,
    browser_type: str = "chromium",
    headless: bool = True,
    allow_local: bool = False,
) -> BrowserInspectionResult:
    """Convenience helper to inspect a website and generate artifacts."""
    inspector = BrowserInspector(
        browser_type=browser_type,
        headless=headless,
        allow_local=allow_local,
    )
    return inspector.inspect(url=url, context=context, output_dir=output_dir)
