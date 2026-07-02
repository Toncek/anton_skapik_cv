import os
import sys
import glob
from playwright.sync_api import sync_playwright

def run_cuj(page):
    page.set_viewport_size({"width": 390, "height": 844})

    # We serve the directory with python
    page.goto("http://localhost:8000/journey/index.html")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    # Scroll down to see images
    page.evaluate("window.scrollBy(0, 800)")
    page.wait_for_timeout(1000)

    page.evaluate("window.scrollBy(0, 800)")
    page.wait_for_timeout(1000)

    page.evaluate("window.scrollBy(0, 800)")
    page.wait_for_timeout(1000)

    # Scroll back to top
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(1000)

    # Take screenshot at the key moment (full page to check everything)
    page.screenshot(path="/app/verification.png", full_page=True)
    page.wait_for_timeout(1000)

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="/app/videos"
        )
        page = context.new_page()
        try:
            run_cuj(page)
        finally:
            context.close()  # MUST close context to save the video
            browser.close()
