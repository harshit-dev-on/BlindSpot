"""Live headed browser scroll test with zero AI tokens."""

import sys
import time

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

from playwright.sync_api import sync_playwright

from blindspot.runtime.browser import EXTRACT_DOM_SNAPSHOT_JS
from blindspot.runtime.provisioning import ensure_browser_engine
from blindspot.utils.console import console


def run_live_scroll_test(target_url: str = "https://www.amazon.com") -> None:
    """Launch a visible Chromium window and smoothly scroll down and back up with 0 AI tokens."""
    ensure_browser_engine("chromium")

    console.print()
    console.print("[bold cyan]●[/bold cyan] [bold white]BlindSpot Live Scroll Demonstration[/bold white] [dim](0 AI tokens)[/dim]")
    console.print(f"  [dim]Target[/dim]    [bold white]{target_url}[/bold white]")
    console.print("  [dim]Engine[/dim]    chromium · [bold cyan]Live Visible Window[/bold cyan]\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context = browser.new_context(
            no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        )
        page = context.new_page()

        console.print("  [dim]→ Navigating to target page...[/dim]")
        try:
            page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            console.print(f"  [dim]Notice:[/dim] [yellow]{e}[/yellow]")

        try:
            dom_snapshot = page.evaluate(EXTRACT_DOM_SNAPSHOT_JS) or {}
            elements = dom_snapshot.get("elements", [])
            dom_html = dom_snapshot.get("dom_html", "")
        except Exception:
            elements = []
            dom_html = ""

        navbar_js = """
        ([targetUrl, rawElements, rawDomHtml]) => {
            const oldHud1 = document.getElementById('__blindspot_test_hud');
            if (oldHud1) oldHud1.remove();
            const oldHud2 = document.getElementById('__blindspot_live_hud');
            if (oldHud2) oldHud2.remove();

            document.documentElement.style.setProperty('margin-top', '40px', 'important');

            let bar = document.getElementById('__blindspot_navbar');
            if (!bar) {
                bar = document.createElement('div');
                bar.id = '__blindspot_navbar';
                bar.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    width: 100%;
                    height: 40px;
                    z-index: 2147483647;
                    background: #090d16;
                    color: #f8fafc;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    font-size: 13px;
                    padding: 0 16px;
                    box-sizing: border-box;
                    border-bottom: 1px solid rgba(56, 189, 248, 0.3);
                    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4);
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    user-select: none;
                    backdrop-filter: blur(10px);
                    cursor: pointer;
                `;
                document.documentElement.appendChild(bar);
            }

            let overlay = document.getElementById('__blindspot_overlay');
            if (!overlay) {
                overlay = document.createElement('div');
                overlay.id = '__blindspot_overlay';
                overlay.style.cssText = `
                    position: fixed;
                    top: 40px;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    width: 100%;
                    height: calc(100vh - 40px);
                    z-index: 2147483646;
                    background: rgba(8, 12, 22, 0.88);
                    backdrop-filter: blur(14px);
                    -webkit-backdrop-filter: blur(14px);
                    display: none;
                    flex-direction: column;
                    padding: 18px 26px;
                    box-sizing: border-box;
                    overflow: hidden;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    color: #f8fafc;
                `;
                document.documentElement.appendChild(overlay);

                window.addEventListener('keydown', (e) => {
                    if (e.key === 'Escape' && overlay.style.display === 'flex') {
                        overlay.style.display = 'none';
                        const pill = document.getElementById('__blindspot_toggle_pill');
                        if (pill) pill.innerText = 'ℹ Details ▾';
                    }
                });
            }

            bar.onclick = () => {
                const ov = document.getElementById('__blindspot_overlay');
                if (!ov) return;
                const isHidden = ov.style.display === 'none' || !ov.style.display;
                ov.style.display = isHidden ? 'flex' : 'none';
                const pill = document.getElementById('__blindspot_toggle_pill');
                if (pill) pill.innerText = isHidden ? '✕ Close ▴' : 'ℹ Details ▾';
            };

            const elements = Array.isArray(rawElements) ? rawElements : [];
            const domHtml = String(rawDomHtml || '');
            const elemCount = elements.length;
            const btnCount = elements.filter(e => e.element_type === 'button' || e.tag === 'button').length;
            const linkCount = elements.filter(e => e.element_type === 'link' || e.tag === 'a').length;
            const inputCount = elements.filter(e => e.element_type === 'input' || e.tag === 'input' || e.tag === 'textarea' || e.tag === 'select').length;
            const domSizeKb = domHtml ? (domHtml.length / 1024).toFixed(1) : '0.0';

            const activeTab = window.__blindspot_active_tab || 'elements';
            const savedSearch = window.__blindspot_search_query || '';

            const renderRows = (elems) => {
                if (!elems || elems.length === 0) {
                    return `
                        <tr>
                            <td colspan="7" style="padding: 32px; text-align: center; color: #94a3b8; font-size: 13px;">
                                🔍 Extracting interactive DOM elements from active page...
                            </td>
                        </tr>
                    `;
                }
                let html = '';
                for (const el of elems) {
                    const ref = el.ref || ('@e' + el.index);
                    const tag = el.tag || '';
                    const elType = el.element_type || 'interactive';
                    const text = (el.text || el.aria_label || el.placeholder || '').trim();
                    const safeText = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
                    const safeTag = tag.replace(/</g, '&lt;').replace(/>/g, '&gt;');

                    let typeColor = '#38bdf8';
                    let typeBg = 'rgba(56, 189, 248, 0.15)';
                    if (elType === 'button') {
                        typeColor = '#c084fc';
                        typeBg = 'rgba(192, 132, 252, 0.15)';
                    } else if (elType === 'link') {
                        typeColor = '#4ade80';
                        typeBg = 'rgba(74, 222, 128, 0.15)';
                    } else if (elType === 'input') {
                        typeColor = '#facc15';
                        typeBg = 'rgba(250, 204, 21, 0.15)';
                    }

                    const attrs = [];
                    if (el.id) attrs.push(`id="<span style="color:#ffffff">${el.id}</span>"`);
                    if (el.name) attrs.push(`name="<span style="color:#ffffff">${el.name}</span>"`);
                    if (el.input_type) attrs.push(`type="<span style="color:#ffffff">${el.input_type}</span>"`);
                    if (el.href) {
                        const cleanHref = el.href.length > 36 ? el.href.slice(0, 36) + '…' : el.href;
                        attrs.push(`href="<span style="color:#38bdf8">${cleanHref}</span>"`);
                    }
                    if (el.placeholder) attrs.push(`ph="<span style="color:#cbd5e1">${el.placeholder}</span>"`);
                    const attrsHtml = attrs.length > 0 ? attrs.join(' ') : '<span style="color:#64748b;">—</span>';
                    const cssHtml = el.css ? `<span style="color: #94a3b8; font-size: 11px;">${el.css}</span>` : '<span style="color:#64748b;">—</span>';
                    const b = el.bounding_box || {};
                    const coords = (b.x !== undefined) ? `x:${b.x}, y:${b.y} <span style="color:#64748b;">(${b.width}×${b.height})</span>` : '—';

                    html += `
                        <tr class="__blindspot_elem_row" style="border-bottom: 1px solid rgba(255,255,255,0.05); transition: background 0.12s;">
                            <td style="padding: 7px 12px; font-family: ui-monospace, Menlo, Consolas, monospace; white-space: nowrap;">
                                <span style="background: rgba(56, 189, 248, 0.18); border: 1px solid rgba(56, 189, 248, 0.4); color: #38bdf8; font-weight: 700; padding: 2px 7px; border-radius: 4px; font-size: 11px;">${ref}</span>
                            </td>
                            <td style="padding: 7px 12px; white-space: nowrap;">
                                <span style="background: ${typeBg}; color: ${typeColor}; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">${elType}</span>
                            </td>
                            <td style="padding: 7px 12px; font-family: monospace; color: #cbd5e1; font-size: 11px; white-space: nowrap;">
                                &lt;${safeTag}&gt;
                            </td>
                            <td style="padding: 7px 12px; max-width: 240px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 500; color: #ffffff;" title="${safeText}">
                                ${safeText ? safeText : '<em style="color:#64748b;">(no text)</em>'}
                            </td>
                            <td style="padding: 7px 12px; font-family: monospace; font-size: 11px; max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #94a3b8;">
                                ${attrsHtml}
                            </td>
                            <td style="padding: 7px 12px; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                                ${cssHtml}
                            </td>
                            <td style="padding: 7px 12px; font-family: monospace; font-size: 11px; color: #94a3b8; white-space: nowrap;">
                                ${coords}
                            </td>
                        </tr>
                    `;
                }
                return html;
            };

            const cleanDomHtml = domHtml ? domHtml.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;') : '(No DOM HTML captured yet)';

            overlay.innerHTML = `
                <div id="__blindspot_info_card" style="width: 100%; height: 100%; display: flex; flex-direction: column; overflow: hidden;">
                    <!-- Full-Screen Top Header -->
                    <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 12px; margin-bottom: 12px; flex-shrink: 0; width: 100%;">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 12px #22c55e;"></span>
                            <div>
                                <h2 style="margin: 0; font-size: 17px; font-weight: 700; color: #ffffff; letter-spacing: 0.5px;">BLINDSPOT ENGINE TELEMETRY</h2>
                                <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">Target: <strong style="color: #38bdf8;">${targetUrl}</strong> · Native Playwright Visible Session</div>
                            </div>
                        </div>
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="background: rgba(34, 197, 94, 0.15); border: 1px solid rgba(34, 197, 94, 0.3); color: #4ade80; padding: 4px 12px; border-radius: 6px; font-size: 11px; font-weight: 600;">ACTIVE SESSION</span>
                            <button id="__blindspot_close_btn" style="background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.18); color: #cbd5e1; padding: 5px 14px; border-radius: 6px; font-size: 11px; font-weight: 600; cursor: pointer;">✕ Close (Esc)</button>
                        </div>
                    </div>

                    <!-- Metrics Ribbon -->
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 12px; flex-shrink: 0; width: 100%;">
                        <div style="background: rgba(255,255,255,0.025); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 8px 14px;">
                            <div style="font-size: 10px; color: #94a3b8; text-transform: uppercase; font-weight: 600;">Extracted DOM Elements</div>
                            <div id="__blindspot_metric_elems" style="font-size: 18px; font-weight: 700; color: #38bdf8; margin-top: 2px;">${elemCount} Elements</div>
                            <div style="font-size: 10px; color: #64748b; margin-top: 1px;">${btnCount} btns · ${linkCount} links · ${inputCount} inputs</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.025); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 8px 14px;">
                            <div style="font-size: 10px; color: #94a3b8; text-transform: uppercase; font-weight: 600;">Clean Semantic DOM Tree</div>
                            <div id="__blindspot_metric_dom" style="font-size: 18px; font-weight: 700; color: #a78bfa; margin-top: 2px;">${domSizeKb} KB</div>
                            <div style="font-size: 10px; color: #64748b; margin-top: 1px;">Cleaned structural HTML tree</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.025); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 8px 14px;">
                            <div style="font-size: 10px; color: #94a3b8; text-transform: uppercase; font-weight: 600;">AI Tokens Burned</div>
                            <div style="font-size: 18px; font-weight: 700; color: #4ade80; margin-top: 2px;">0 Tokens</div>
                            <div style="font-size: 10px; color: #64748b; margin-top: 1px;">Direct DOM execution · Zero LLM latency</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.025); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 8px 14px;">
                            <div style="font-size: 10px; color: #94a3b8; text-transform: uppercase; font-weight: 600;">Runtime Engine</div>
                            <div style="font-size: 18px; font-weight: 700; color: #e2e8f0; margin-top: 2px;">Maximized Window</div>
                            <div style="font-size: 10px; color: #64748b; margin-top: 1px;">Native host browser window</div>
                        </div>
                    </div>

                    <!-- Tabs Bar & Search Box -->
                    <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 8px; margin-bottom: 12px; flex-shrink: 0;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <button id="__blindspot_tab_elements" style="background: ${activeTab === 'elements' ? '#0284c7' : 'rgba(255,255,255,0.06)'}; border: 1px solid ${activeTab === 'elements' ? '#38bdf8' : 'rgba(255,255,255,0.1)'}; color: ${activeTab === 'elements' ? '#ffffff' : '#94a3b8'}; padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.15s;">🎯 Extracted Interactive Elements (${elemCount})</button>
                            <button id="__blindspot_tab_dom" style="background: ${activeTab === 'dom' ? '#0284c7' : 'rgba(255,255,255,0.06)'}; border: 1px solid ${activeTab === 'dom' ? '#38bdf8' : 'rgba(255,255,255,0.1)'}; color: ${activeTab === 'dom' ? '#ffffff' : '#94a3b8'}; padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.15s;">📑 Cleaned Semantic DOM HTML</button>
                            <button id="__blindspot_tab_telemetry" style="background: ${activeTab === 'telemetry' ? '#0284c7' : 'rgba(255,255,255,0.06)'}; border: 1px solid ${activeTab === 'telemetry' ? '#38bdf8' : 'rgba(255,255,255,0.1)'}; color: ${activeTab === 'telemetry' ? '#ffffff' : '#94a3b8'}; padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.15s;">⚡ Live Timeline & Details</button>
                        </div>
                        <div id="__blindspot_search_container" style="display: ${activeTab === 'elements' ? 'flex' : 'none'}; align-items: center; gap: 8px;">
                            <input id="__blindspot_elem_search" type="text" value="${savedSearch}" placeholder="🔍 Filter elements by text, ref, tag, id, type..." style="background: rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.15); border-radius: 6px; color: #ffffff; padding: 5px 12px; font-size: 12px; width: 320px; outline: none;" />
                        </div>
                    </div>

                    <!-- Tab 1: Extracted Elements Inventory Table -->
                    <div id="__blindspot_panel_elements" style="flex: 1; display: ${activeTab === 'elements' ? 'flex' : 'none'}; flex-direction: column; overflow: hidden; min-height: 0;">
                        <div style="flex: 1; overflow-y: auto; border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; background: rgba(0, 0, 0, 0.4);">
                            <table style="width: 100%; border-collapse: collapse; font-size: 12px; text-align: left;">
                                <thead style="position: sticky; top: 0; background: #0c1222; border-bottom: 1px solid rgba(255,255,255,0.12); z-index: 2;">
                                    <tr>
                                        <th style="padding: 9px 12px; color: #94a3b8; font-weight: 600; width: 65px;">Ref</th>
                                        <th style="padding: 9px 12px; color: #94a3b8; font-weight: 600; width: 85px;">Type</th>
                                        <th style="padding: 9px 12px; color: #94a3b8; font-weight: 600; width: 90px;">Tag</th>
                                        <th style="padding: 9px 12px; color: #94a3b8; font-weight: 600;">Text / Accessible Label</th>
                                        <th style="padding: 9px 12px; color: #94a3b8; font-weight: 600;">Key Attributes & Target</th>
                                        <th style="padding: 9px 12px; color: #94a3b8; font-weight: 600;">Computed CSS Styling</th>
                                        <th style="padding: 9px 12px; color: #94a3b8; font-weight: 600; width: 150px;">Viewport Coords</th>
                                    </tr>
                                </thead>
                                <tbody id="__blindspot_elem_tbody">
                                    ${renderRows(elements)}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Tab 2: Cleaned Semantic DOM HTML Tree -->
                    <div id="__blindspot_panel_dom" style="flex: 1; display: ${activeTab === 'dom' ? 'flex' : 'none'}; flex-direction: column; overflow: hidden; min-height: 0;">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; font-size: 12px; color: #94a3b8; flex-shrink: 0;">
                            <span>Clean semantic HTML structure of target page:</span>
                            <button id="__blindspot_copy_dom_btn" style="background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.35); color: #38bdf8; padding: 4px 12px; border-radius: 6px; font-size: 11px; font-weight: 600; cursor: pointer;">📋 Copy HTML</button>
                        </div>
                        <div style="flex: 1; overflow: auto; background: rgba(0, 0, 0, 0.55); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 14px 18px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 12px; line-height: 1.6; color: #e2e8f0; white-space: pre-wrap; word-break: break-all;">
                            <code id="__blindspot_dom_code">${cleanDomHtml}</code>
                        </div>
                    </div>

                    <!-- Tab 3: Timeline & Details -->
                    <div id="__blindspot_panel_telemetry" style="flex: 1; display: ${activeTab === 'telemetry' ? 'flex' : 'none'}; flex-direction: column; overflow-y: auto; min-height: 0; gap: 14px;">
                        <div style="display: grid; grid-template-columns: 1fr 1.3fr; gap: 14px; flex: 1;">
                            <div style="display: flex; flex-direction: column; gap: 12px;">
                                <div style="background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 8px; padding: 14px 18px;">
                                    <div style="display: flex; align-items: center; justify-content: space-between;">
                                        <span style="font-size: 10px; color: #38bdf8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">Active Status</span>
                                        <span style="background: rgba(34, 197, 94, 0.2); color: #4ade80; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 600;">ACTIVE</span>
                                    </div>
                                    <div id="__blindspot_modal_msg" style="font-size: 14px; font-weight: 600; color: #ffffff; margin-top: 6px;">Initializing live scroll...</div>
                                </div>
                                <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 14px 18px; flex: 1;">
                                    <div style="font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">Inspection Architecture</div>
                                    <div style="font-size: 12px; color: #cbd5e1; line-height: 1.7;">
                                        • <strong>Zero Token Burn</strong>: Directly scrolls and analyzes the DOM without consuming vision tokens.<br>
                                        • <strong>Full-Screen Real-Time HUD</strong>: Displays comprehensive telemetry and extracted DOM across the viewport.<br>
                                        • <strong>Continuous Execution</strong>: The background website continues smoothly scrolling and rendering behind this screen.<br>
                                        • <strong>Native Playwright</strong>: Runs directly on host browser without requiring Docker.
                                    </div>
                                </div>
                            </div>
                            <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 14px 18px; display: flex; flex-direction: column;">
                                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
                                    <span style="font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px;">Real-Time Execution Timeline</span>
                                    <span style="font-size: 10px; color: #64748b;">Live Stream</span>
                                </div>
                                <div id="__blindspot_modal_log" style="font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 12px; flex: 1; min-height: 180px; max-height: 360px; overflow-y: auto; color: #cbd5e1; line-height: 1.8;">
                                    <div><span style="color: #64748b;">[0.0s]</span> <span style="color: #38bdf8;">›</span> Navigated to ${targetUrl}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Full-Width Footer -->
                    <div style="border-top: 1px solid rgba(255,255,255,0.06); padding-top: 8px; margin-top: 8px; display: flex; align-items: center; justify-content: space-between; font-size: 11px; color: #64748b; flex-shrink: 0; width: 100%;">
                        <div>💡 <strong>Full Screen DOM View</strong> · Click navbar or press Esc to return · The website continues running smoothly in the background.</div>
                        <div>${elemCount} elements extracted · ${domSizeKb} KB semantic HTML</div>
                    </div>
                </div>
            `;

            // Wire tabs
            const tabElemBtn = document.getElementById('__blindspot_tab_elements');
            const tabDomBtn = document.getElementById('__blindspot_tab_dom');
            const tabTelemBtn = document.getElementById('__blindspot_tab_telemetry');
            const pElem = document.getElementById('__blindspot_panel_elements');
            const pDom = document.getElementById('__blindspot_panel_dom');
            const pTelem = document.getElementById('__blindspot_panel_telemetry');
            const searchBox = document.getElementById('__blindspot_search_container');

            const setTab = (t) => {
                window.__blindspot_active_tab = t;
                if (pElem) pElem.style.display = t === 'elements' ? 'flex' : 'none';
                if (pDom) pDom.style.display = t === 'dom' ? 'flex' : 'none';
                if (pTelem) pTelem.style.display = t === 'telemetry' ? 'flex' : 'none';
                if (searchBox) searchBox.style.display = t === 'elements' ? 'flex' : 'none';

                const updateBtn = (btn, active) => {
                    if (!btn) return;
                    btn.style.background = active ? '#0284c7' : 'rgba(255,255,255,0.06)';
                    btn.style.borderColor = active ? '#38bdf8' : 'rgba(255,255,255,0.1)';
                    btn.style.color = active ? '#ffffff' : '#94a3b8';
                };
                updateBtn(tabElemBtn, t === 'elements');
                updateBtn(tabDomBtn, t === 'dom');
                updateBtn(tabTelemBtn, t === 'telemetry');
            };

            if (tabElemBtn) tabElemBtn.onclick = () => setTab('elements');
            if (tabDomBtn) tabDomBtn.onclick = () => setTab('dom');
            if (tabTelemBtn) tabTelemBtn.onclick = () => setTab('telemetry');

            // Wire search filter
            const searchInput = document.getElementById('__blindspot_elem_search');
            if (searchInput) {
                const filterTable = (q) => {
                    window.__blindspot_search_query = q;
                    const query = q.toLowerCase().trim();
                    const rows = document.querySelectorAll('.__blindspot_elem_row');
                    rows.forEach(r => {
                        const txt = r.innerText.toLowerCase();
                        r.style.display = (!query || txt.includes(query)) ? '' : 'none';
                    });
                };
                searchInput.addEventListener('input', (e) => filterTable(e.target.value));
                if (savedSearch) filterTable(savedSearch);
            }

            // Wire copy button
            const copyBtn = document.getElementById('__blindspot_copy_dom_btn');
            if (copyBtn) {
                copyBtn.onclick = () => {
                    if (navigator.clipboard && navigator.clipboard.writeText) {
                        navigator.clipboard.writeText(domHtml || '');
                        copyBtn.innerText = '✔ Copied!';
                        setTimeout(() => { copyBtn.innerText = '📋 Copy HTML'; }, 2000);
                    }
                };
            }

            const closeBtn = document.getElementById('__blindspot_close_btn');
            if (closeBtn) {
                closeBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    overlay.style.display = 'none';
                    const pill = document.getElementById('__blindspot_toggle_pill');
                    if (pill) pill.innerText = 'ℹ Details ▾';
                });
            }

            bar.innerHTML = `
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 10px #22c55e;"></span>
                    <strong style="color: #38bdf8; font-size: 13px; letter-spacing: 0.5px;">BLINDSPOT</strong>
                    <span style="color: #475569;">|</span>
                    <span style="color: #cbd5e1; font-weight: 500;">Live Scroll Test</span>
                    <span style="color: #64748b; font-size: 11px;">(0 AI Tokens)</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px; font-size: 12px; color: #94a3b8; background: rgba(255,255,255,0.04); padding: 4px 14px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.08);">
                    <strong style="color: #38bdf8;">Status:</strong>
                    <span id="__blindspot_nav_msg" style="color: #e2e8f0;">Initializing live scroll...</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="background: rgba(34, 197, 94, 0.15); border: 1px solid rgba(34, 197, 94, 0.3); color: #4ade80; padding: 2px 10px; border-radius: 12px; font-size: 11px; font-weight: 600;">ACTIVE</span>
                    <span id="__blindspot_toggle_pill" style="background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.35); color: #38bdf8; padding: 2px 10px; border-radius: 12px; font-size: 11px; font-weight: 600;">ℹ Details ▾</span>
                </div>
            `;
        };
        """
        try:
            page.evaluate(navbar_js, [target_url, elements, dom_html])
        except Exception:
            pass

        start_ts = time.time()

        def update_navbar(message: str) -> None:
            msg_escaped = message.replace("'", "\\'").replace('"', '\\"')
            elapsed = f"{time.time() - start_ts:.1f}s"
            try:
                page.evaluate(
                    f"""() => {{
                        const el = document.getElementById('__blindspot_nav_msg');
                        if (el) el.innerText = '{msg_escaped}';
                        const modalMsg = document.getElementById('__blindspot_modal_msg');
                        if (modalMsg) modalMsg.innerText = '{msg_escaped}';
                        const log = document.getElementById('__blindspot_modal_log');
                        if (log) {{
                            const row = document.createElement('div');
                            row.innerHTML = `<span style="color: #64748b;">[{elapsed}]</span> <span style="color: #38bdf8;">›</span> {msg_escaped}`;
                            log.appendChild(row);
                            log.scrollTop = log.scrollHeight;
                        }}
                    }}()"""
                )
            except Exception:
                pass
            console.print(f"  [bold cyan]›[/bold cyan] [white]{message}[/white]")

        time.sleep(1.5)
        update_navbar("Action: Scrolling down smoothly...")

        total_scroll_distance = 2400
        step_size = 350
        current_scroll = 0

        while current_scroll < total_scroll_distance:
            current_scroll += step_size
            try:
                page.evaluate(f"window.scrollTo({{ top: {current_scroll}, behavior: 'smooth' }});")
            except Exception:
                pass
            time.sleep(0.7)

        update_navbar("Reached mid-page. Observing dynamic content...")
        time.sleep(2.0)

        update_navbar("Action: Scrolling further down toward footer...")
        while current_scroll < 4500:
            current_scroll += step_size
            try:
                page.evaluate(f"window.scrollTo({{ top: {current_scroll}, behavior: 'smooth' }});")
            except Exception:
                pass
            time.sleep(0.6)

        time.sleep(1.5)
        update_navbar("Action: Smoothly scrolling back to top of page...")
        try:
            page.evaluate("window.scrollTo({ top: 0, behavior: 'smooth' });")
        except Exception:
            pass
        time.sleep(2.5)

        update_navbar("Live scroll test completed successfully! Closing in 3s...")
        time.sleep(3.0)

        context.close()
        browser.close()
        console.print("\n[bold green]✔ Live scroll test finished cleanly.[/bold green]\n")
