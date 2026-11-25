#!/usr/bin/env python3
"""End-to-end Playwright and privacy verification suite for anton_skapik_cv."""

from __future__ import annotations

import argparse
import http.server
import json
import os
import pathlib
import re
import shutil
import socketserver
import sys
import tempfile
import threading
import urllib.request
import xml.etree.ElementTree as ET

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _ensure_working_playwright_interpreter() -> None:
    """Re-exec with repo .venv Python if system python3-playwright lacks its driver."""
    venv_python = REPO_ROOT / ".venv" / "bin" / "python"
    if not venv_python.is_file():
        return
    if pathlib.Path(sys.executable).resolve() == venv_python.resolve():
        return
    try:
        from playwright._impl._driver import compute_driver_executable

        driver_exec = compute_driver_executable()
        driver_target = driver_exec[1] if isinstance(driver_exec, tuple) and len(driver_exec) > 1 else driver_exec[0]
        if driver_target and not pathlib.Path(driver_target).exists():
            os.execv(str(venv_python), [str(venv_python), __file__, *sys.argv[1:]])
    except Exception:
        os.execv(str(venv_python), [str(venv_python), __file__, *sys.argv[1:]])


_ensure_working_playwright_interpreter()

from playwright.sync_api import sync_playwright  # noqa: E402


def launch_chromium(p):
    """Launch Playwright's Chromium or fall back to system Chromium when absent."""
    try:
        return p.chromium.launch()
    except Exception:
        for candidate in ("chromium", "chromium-browser", "google-chrome"):
            exe = shutil.which(candidate)
            if exe:
                return p.chromium.launch(executable_path=exe, args=["--no-sandbox"])
        raise


class QuietStaticHandler(http.server.SimpleHTTPRequestHandler):
    """Serve files from REPO_ROOT without noisy HTTP access logs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(REPO_ROOT), **kwargs)

    def log_message(self, format, *args):  # noqa: A002
        pass


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def start_ephemeral_server() -> tuple[ThreadedTCPServer, int]:
    server = ThreadedTCPServer(("127.0.0.1", 0), QuietStaticHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port


def assert_static_privacy_and_pdf(base_url: str) -> None:
    # 1. Verify cv.pdf over HTTP
    with urllib.request.urlopen(f"{base_url}/cv.pdf", timeout=10) as resp:
        assert resp.status == 200, f"Expected HTTP 200 for /cv.pdf, got {resp.status}"
        pdf_bytes = resp.read()
    assert pdf_bytes.startswith(b"%PDF-"), "cv.pdf does not start with %PDF-"
    assert len(pdf_bytes) > 15 * 1024, f"cv.pdf too small ({len(pdf_bytes)} bytes)"

    # 2. Verify robots.txt and sitemap.xml
    robots_text = (REPO_ROOT / "robots.txt").read_text(encoding="utf-8")
    assert re.search(r"(?im)^\s*Disallow:\s*/journey/\s*$", robots_text), (
        "robots.txt must disallow /journey/"
    )

    sitemap_tree = ET.parse(REPO_ROOT / "sitemap.xml")
    locs = [el.text.strip() for el in sitemap_tree.iter() if el.tag.endswith("loc") and el.text]
    assert locs, "sitemap.xml has no <loc> entries"
    assert not any("journey" in loc.lower() for loc in locs), (
        "sitemap.xml must exclude /journey/"
    )

    # 3. Verify public pages have zero leakage of private terms
    forbidden_terms = ("journey", "stickers", "anton_svk", "anton_in_asia", "sangsom")
    for rel in ("index.html", "apps/index.html"):
        raw = (REPO_ROOT / rel).read_text(encoding="utf-8").lower()
        for term in forbidden_terms:
            assert term not in raw, f"Privacy breach: '{term}' found in {rel}"

    # 4. Verify unlisted pages declare noindex, nofollow and never link out to CV/apps
    for rel in ("journey/index.html", "journey/stickers/index.html"):
        raw = (REPO_ROOT / rel).read_text(encoding="utf-8")
        assert re.search(
            r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex[^"\']*nofollow',
            raw,
            re.IGNORECASE,
        ), f"{rel} missing noindex, nofollow meta tag"

        hrefs = re.findall(r'<a[^>]+href=["\']([^"\']+)["\']', raw, flags=re.IGNORECASE)
        for href in hrefs:
            low = href.lower()
            if low.startswith(("http://", "https://", "mailto:", "tel:", "#")):
                # External URLs must not point to public CV or /apps/
                assert "anton_skapik_cv/apps" not in low, f"{rel} links out to apps: {href}"
                assert not low.rstrip("/").endswith("anton_skapik_cv"), (
                    f"{rel} links out to CV root: {href}"
                )
            else:
                # Relative links inside /journey/stickers/ may go to ../ (which is /journey/),
                # but must never traverse out to CV root (../../) or /apps/
                assert "apps" not in low, f"{rel} links to apps: {href}"
                assert not low.startswith("../../"), f"{rel} escapes /journey/: {href}"
                if rel == "journey/index.html":
                    assert not low.startswith("../"), f"{rel} escapes /journey/: {href}"


def scroll_and_check_images_and_overflow(page, route_label: str) -> None:
    # Scroll down in steps so loading="lazy" images load before inspection
    total_height = page.evaluate("document.body.scrollHeight")
    for y in range(0, total_height + 400, 450):
        page.evaluate(f"window.scrollTo(0, {y})")
        page.wait_for_timeout(60)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(120)

    overflow = page.evaluate(
        "() => ({ scrollWidth: document.documentElement.scrollWidth, innerWidth: window.innerWidth })"
    )
    assert overflow["scrollWidth"] <= overflow["innerWidth"] + 1, (
        f"Horizontal overflow on {route_label}: scrollWidth={overflow['scrollWidth']} > innerWidth={overflow['innerWidth']}"
    )

    broken_imgs = page.evaluate(
        """() => {
            return Array.from(document.querySelectorAll('img')).filter((img) => {
                if (!img.getAttribute('src') && img.closest('.lightbox')) return false;
                const style = window.getComputedStyle(img);
                if (style.display === 'none') return false;
                return !img.complete || img.naturalWidth <= 0;
            }).map((img) => img.getAttribute('src'));
        }"""
    )
    assert not broken_imgs, f"Broken images on {route_label}: {broken_imgs}"


def check_routes_desktop_and_mobile(browser, base_url: str, screenshots_dir: pathlib.Path) -> None:
    routes = [
        ("cv", "/"),
        ("apps", "/apps/"),
        ("journey", "/journey/"),
        ("stickers", "/journey/stickers/"),
    ]
    viewports = [
        ("desktop", {"width": 1280, "height": 900}),
        ("mobile", {"width": 390, "height": 844}),
    ]

    for vp_name, vp_size in viewports:
        context = browser.new_context(viewport=vp_size)
        page = context.new_page()
        for slug, path in routes:
            console_errors: list[str] = []
            page_errors: list[str] = []

            def on_console(msg):
                if msg.type == "error":
                    console_errors.append(msg.text)

            page.on("console", on_console)
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))

            resp = page.goto(f"{base_url}{path}", wait_until="networkidle")
            assert resp is not None and resp.status == 200, (
                f"Expected HTTP 200 for {path}, got {resp.status if resp else None}"
            )

            scroll_and_check_images_and_overflow(page, f"{vp_name}:{path}")

            # Verify no console/page errors
            assert not console_errors, f"Console errors on {vp_name}:{path}: {console_errors}"
            assert not page_errors, f"Page errors on {vp_name}:{path}: {page_errors}"

            shot_path = screenshots_dir / f"{vp_name}_{slug}.png"
            page.screenshot(path=str(shot_path), full_page=True)

            page.remove_listener("console", on_console)

        context.close()


def test_theme_toggles(browser, base_url: str) -> None:
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    page = context.new_page()

    # CV & Apps share localStorage('theme')
    page.goto(f"{base_url}/", wait_until="networkidle")
    initial = page.locator("html").get_attribute("data-theme")
    page.click("#theme-toggle")
    toggled = page.locator("html").get_attribute("data-theme")
    assert toggled != initial, "Theme toggle did not change data-theme on /"
    stored = page.evaluate("localStorage.getItem('theme')")
    assert stored == toggled, f"Expected localStorage('theme')={toggled}, got {stored}"

    page.goto(f"{base_url}/apps/", wait_until="networkidle")
    assert page.locator("html").get_attribute("data-theme") == toggled, (
        "/apps/ did not sync saved theme from localStorage"
    )
    page.click("#theme-toggle")
    assert page.locator("html").get_attribute("data-theme") == initial, (
        "Theme toggle did not switch back on /apps/"
    )

    # Journey & Stickers theme toggles
    for path in ("/journey/", "/journey/stickers/"):
        page.goto(f"{base_url}{path}", wait_until="networkidle")
        cur = page.locator("html").get_attribute("data-theme")
        page.click("#theme-toggle")
        nxt = page.locator("html").get_attribute("data-theme")
        assert nxt != cur, f"Theme toggle failed on {path}"

    context.close()


def test_apps_interactions(browser, base_url: str) -> None:
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    page = context.new_page()

    # Mock FormSubmit endpoint
    submitted_payloads = []

    def handle_formsubmit(route):
        body = route.request.post_data or "{}"
        submitted_payloads.append(json.loads(body))
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"success": "true", "message": "Mocked OK"}),
        )

    page.route("https://formsubmit.co/**", handle_formsubmit)

    page.goto(f"{base_url}/apps/", wait_until="networkidle")

    # 1. Category filter pills
    page.click('.filter-pill[data-filter="games"]')
    assert "2 projects" in page.locator("#filter-status").inner_text(), (
        "Expected 2 projects when filtering by games"
    )
    page.click('.filter-pill[data-filter="nlp"]')
    assert "3 projects" in page.locator("#filter-status").inner_text(), (
        "Expected 3 projects when filtering by nlp"
    )
    page.click('.filter-pill[data-filter="all"]')
    assert "7 projects" in page.locator("#filter-status").inner_text(), (
        "Expected 7 projects when filtering by all"
    )

    # 2. KurveCounter slider update
    slider = page.locator("#kurve-lean-slider")
    slider.fill("45")
    slider.dispatch_event("input")
    assert page.locator("#kurve-angle-readout").inner_text() == "R 45°"
    assert page.locator("#kurve-right-peak").inner_text() == "+45°"
    assert page.locator("#kurve-lat-g").inner_text() == "1.00 G"
    assert page.locator("#kurve-service-status").inner_text() == "DUE_SOON"

    slider.fill("-30")
    slider.dispatch_event("input")
    assert page.locator("#kurve-angle-readout").inner_text() == "L 30°"
    assert page.locator("#kurve-left-peak").inner_text() == "-30°"
    assert page.locator("#kurve-service-status").inner_text() == "OK"

    # 3. Thajčina syllable toggle
    page.click('.word-tab[data-thai-word="kafe"]')
    assert "gá-fé jen" in page.locator("#xray-summary").inner_text()
    page.click('.word-tab[data-thai-word="khobkhun"]')
    assert "chòp-khun mâk" in page.locator("#xray-summary").inner_text()

    # 4. Spaceless Syndicate slicer toggle & reset
    page.click('.laser-cut-btn[data-cut-index="0"]')
    assert page.locator("#laser-progress").inner_text() == "1 / 4 cuts placed"
    page.click("#laser-slice-all")
    assert page.locator("#laser-progress").inner_text() == "4 / 4 cuts placed"
    assert "the pier" in page.locator("#laser-glosses").inner_text()
    page.click("#laser-reset")
    assert page.locator("#laser-progress").inner_text() == "0 / 4 cuts placed"

    # 5. Lightbox & thumbnail switcher
    page.click('button[data-src="../assets/apps/icytower-skills.webp"]')
    assert "icytower-skills.webp" in (page.locator("#icy-stage-img").get_attribute("src") or "")
    page.click("#icy-stage-trigger")
    assert "is-open" in (page.locator("#lightbox").get_attribute("class") or "")
    page.click("#lightbox-close")
    assert "is-open" not in (page.locator("#lightbox").get_attribute("class") or "")

    # 6. Empty-apps validation
    page.fill("#beta-email", "tester@example.com")
    page.click("#beta-submit-btn")
    assert "is-visible" in (page.locator("#beta-error").get_attribute("class") or ""), (
        "Expected validation error when no apps are selected"
    )
    assert len(submitted_payloads) == 0

    # 7. [data-join-app] pre-selection + mocked submit success
    page.click('[data-join-app="KurveCounter"]')
    assert page.locator('input[name="apps"][value="KurveCounter"]').is_checked()
    page.fill("#beta-email", "rider@example.com")
    page.fill("#beta-name", "MotoTester")
    page.click("#beta-submit-btn")

    page.locator("#beta-success.is-visible").wait_for(state="visible", timeout=5000)
    assert "KurveCounter" in page.locator("#beta-success").inner_text()
    assert len(submitted_payloads) == 1
    assert submitted_payloads[0]["email"] == "rider@example.com"

    context.close()


def test_journey_and_stickers_interactions(browser, base_url: str) -> None:
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    page = context.new_page()

    # /journey/ Line ID copy button
    page.goto(f"{base_url}/journey/", wait_until="networkidle")
    page.click("#copy-line-btn")
    page.wait_for_function(
        "() => document.getElementById('copy-line-btn').textContent === 'Copied!'",
        timeout=3000,
    )
    assert "anton_svk" in page.locator("#copy-status").inner_text()

    # /journey/stickers/ surface switcher + lightbox
    page.goto(f"{base_url}/journey/stickers/", wait_until="networkidle")
    page.click('.surface-btn[data-surface-choice="black-pannier"]')
    assert page.locator("body").get_attribute("data-surface") == "black-pannier"
    page.click('.surface-btn[data-surface-choice="silver-topbox"]')
    assert page.locator("body").get_attribute("data-surface") == "silver-topbox"

    page.locator(".zoom-btn").first.click()
    assert "is-open" in (page.locator("#lightbox").get_attribute("class") or "")
    page.click("#lightbox-close")
    assert "is-open" not in (page.locator("#lightbox").get_attribute("class") or "")

    context.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify anton_skapik_cv static site.")
    parser.add_argument(
        "--screenshots-dir",
        type=pathlib.Path,
        default=None,
        help="Directory to write desktop_*.png and mobile_*.png screenshots.",
    )
    args = parser.parse_args()

    screenshots_dir = (
        args.screenshots_dir.resolve()
        if args.screenshots_dir is not None
        else pathlib.Path(tempfile.mkdtemp(prefix="cv_verify_"))
    )
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    server, port = start_ephemeral_server()
    base_url = f"http://127.0.0.1:{port}"
    try:
        assert_static_privacy_and_pdf(base_url)
        with sync_playwright() as p:
            browser = launch_chromium(p)
            try:
                check_routes_desktop_and_mobile(browser, base_url, screenshots_dir)
                test_theme_toggles(browser, base_url)
                test_apps_interactions(browser, base_url)
                test_journey_and_stickers_interactions(browser, base_url)
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()

    print(f"All Playwright, privacy, PDF, and interactive checks passed. Screenshots: {screenshots_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
