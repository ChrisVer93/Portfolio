#!/usr/bin/env python3
"""Capture genuine Loss Lab UI screens and replace manual-only mockups.

This runs the checked-out application in Chromium with the built-in synthetic
example study. No engineering results are represented as measured data.
"""
from __future__ import annotations

import functools
import http.server
from pathlib import Path
import re
import threading
import zipfile

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "dist"
APP = DIST / "tools" / "loss-lab"
IMAGES = APP / "screenshots"
MANUAL = APP / "manual.html"
IMAGES.mkdir(parents=True, exist_ok=True)

# The order follows the 23 existing annotated screen-guide figures.
GUIDE_IMAGES = [
    "overview", "waveforms", "waveforms-conditions", "components-settings",
    "components-settings", "components-curves", "overview-settings",
    "components-curves", "components-settings", "components-settings",
    "capacitor-curves", "components-thermal", "results-breakdown",
    "results-debug", "results-inspect", "checks", "results-range",
    "help", "results-inspect", "diode-curves", "capacitor-curves",
    "inductor-curves", "components-thermal",
]

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass

handler = functools.partial(QuietHandler, directory=str(DIST))
server = http.server.ThreadingHTTPServer(("127.0.0.1", 8765), handler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()

captures: set[str] = set()

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
    page = browser.new_page(
        viewport={"width": 1536, "height": 950}, device_scale_factor=1,
        reduced_motion="reduce",
    )
    page.on("dialog", lambda dialog: dialog.accept())
    page.goto("http://127.0.0.1:8765/tools/loss-lab/index.html#overview",
              wait_until="networkidle", timeout=90000)
    page.locator("#page .metrics").wait_for(timeout=30000)
    # The real app loads the bundled synthetic demo by default, then runs it.
    # Wait for the worker to finish so result captures contain real UI charts.
    try:
        page.wait_for_function(
            "() => document.querySelector('#status')?.textContent.includes('complete') || "
            "document.querySelector('#status')?.textContent.includes('Complete') || "
            "document.querySelector('#status')?.textContent.includes('finished')",
            timeout=50000,
        )
    except Exception:
        pass
    page.add_style_tag(content="#toast {display:none!important} "
                               "* {scroll-behavior:auto!important;animation:none!important}")

    def nav(name: str):
        page.locator('nav a[data-page="' + name + '"]').click()
        page.wait_for_timeout(350)

    def scroll_panel(text: str):
        el = page.locator("#page .panel").filter(
            has=page.get_by_role("heading", name=text, exact=False)
        ).first
        if el.count():
            el.scroll_into_view_if_needed(timeout=5000)
            page.wait_for_timeout(200)

    def shot(name: str):
        page.screenshot(path=str(IMAGES / (name + ".png")), animations="disabled")
        size = (IMAGES / (name + ".png")).stat().st_size
        if size < 9000:
            raise RuntimeError(f"Unusually small screenshot {name}: {size} bytes")
        captures.add(name)
        print("Captured", name, size)

    nav("overview")
    page.evaluate("window.scrollTo(0,0)")
    shot("overview")
    scroll_panel("Analysis settings")
    shot("overview-settings")

    nav("waveforms")
    page.evaluate("window.scrollTo(0,0)")
    shot("waveforms")
    scroll_panel("Operating conditions")
    shot("waveforms-conditions")

    nav("devices")
    page.evaluate("window.scrollTo(0,0)")
    shot("components-settings")
    page.locator('[data-subtab="curves"]').click()
    shot("components-curves")
    page.locator('[data-subtab="thermal"]').click()
    shot("components-thermal")

    for selector, name in [
        ("D1", "diode-curves"),
        ("C1", "capacitor-curves"),
        ("L1", "inductor-curves"),
    ]:
        nav("devices")
        page.locator(".device-nav button").filter(has_text=selector).first.click()
        page.locator('[data-subtab="curves"]').click()
        shot(name)

    nav("checks")
    page.evaluate("window.scrollTo(0,0)")
    shot("checks")

    nav("results")
    page.wait_for_timeout(700)
    if not page.locator(".results-scope").count():
        # A reload may have interrupted the automatic example calculation.
        page.locator("#run").click()
        page.locator(".results-scope").wait_for(timeout=90000)
    page.locator('[data-results-scope="range"]').click()
    page.evaluate("window.scrollTo(0,0)")
    shot("results-range")
    scroll_panel("Selected component losses · whole operating range")
    shot("results-breakdown")
    page.locator('[data-results-scope="point"]').click()
    page.evaluate("window.scrollTo(0,0)")
    shot("results-point")
    page.locator('[data-results-tab="inspect"]').click()
    scroll_panel("Selected component losses")
    shot("results-inspect")
    page.locator('[data-results-tab="debug"]').click()
    scroll_panel("Debug: queried curves")
    shot("results-debug")
    page.locator('[data-results-tab="models"]').click()
    scroll_panel("Characteristic coverage")
    shot("results-models")

    nav("overview")
    page.locator("#helpOpen").click()
    page.wait_for_timeout(300)
    shot("help")
    browser.close()

server.shutdown()

for name in GUIDE_IMAGES:
    if name not in captures:
        raise RuntimeError(f"Required capture missing: {name}")

html = MANUAL.read_text(encoding="utf-8")
figure_re = re.compile(r'<figure class="doc-screen-guide">[\s\S]*?</figure>')
figures = figure_re.findall(html)
if len(figures) != len(GUIDE_IMAGES):
    raise RuntimeError(f"Expected {len(GUIDE_IMAGES)} screen guides, found {len(figures)}")

def replace_figure(match):
    index = replace_figure.index
    replace_figure.index += 1
    name = GUIDE_IMAGES[index]
    fig = match.group(0)
    title_match = re.search(r'<figcaption><strong>(.*?)</strong></figcaption>', fig)
    title = re.sub(r'<[^>]*>', '', title_match.group(1)) if title_match else name
    new_image = ('<div class="doc-screen-scroll"><img class="doc-tool-screenshot" '
                 f'src="screenshots/{name}.png" loading="lazy" '
                 f'alt="Actual Converter Loss Lab interface: {title}"></div>')
    fig, n = re.subn(r'<div class="doc-screen-scroll"><svg\b[\s\S]*?</svg></div>',
                     lambda _: new_image, fig, count=1)
    if n != 1:
        raise RuntimeError(f"Could not locate schematic in screen guide {index + 1}")
    fig, _ = re.subn(r'<p class="caption">Annotated UI illustration[\s\S]*?</p>',
                    '<p class="caption">Actual screenshot of Converter Loss Lab 2.5.5 '
                    'using its built-in synthetic demonstration study. '
                    'The guidance below describes associated controls; '
                    'some controls may be further down the page. '
                    'Example results are not laboratory measurements.</p>',
                    fig, count=1)
    fig = fig.replace('<ol>', '<ul>').replace('</ol>', '</ul>')
    return fig

replace_figure.index = 0
updated = figure_re.sub(replace_figure, html)
if replace_figure.index != len(GUIDE_IMAGES):
    raise RuntimeError("Not all screen guides were replaced")

# Preserve the technical demonstration plots, formulas and existing explanations.
extra_style = (' .doc-screen-guide .doc-screen-scroll{overflow:visible}'
               ' .doc-screen-guide .doc-tool-screenshot{display:block;width:100%;'
               'min-width:0;max-width:100%;height:auto;'
               'border:1px solid #b9c8d2;border-radius:9px;'
               'box-shadow:0 4px 18px #1933431a}'
               ' @media print{.doc-screen-guide .doc-tool-screenshot{'
               'max-width:170mm;max-height:132mm;object-fit:contain;box-shadow:none}}')
if extra_style not in updated:
    updated = updated.replace('</style>', extra_style + '</style>', 1)
updated = updated.replace(
    'href="manual.html" download="Loss_Lab_Manual.html"',
    'href="Loss_Lab_Manual_Offline.zip" download="Loss_Lab_Manual_Offline.zip"'
)
updated = updated.replace('Download offline manual', 'Download offline manual + screenshots')
MANUAL.write_text(updated, encoding="utf-8")

archive = APP / "Loss_Lab_Manual_Offline.zip"
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=8) as z:
    z.write(MANUAL, "manual.html")
    for name in sorted(captures):
        z.write(IMAGES / (name + ".png"), "screenshots/" + name + ".png")

print(f"Updated {len(GUIDE_IMAGES)} manual screen guides "
      f"with {len(captures)} genuine screenshots; offline ZIP {archive.stat().st_size} bytes.")
