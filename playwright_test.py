from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 375, "height": 812})
    page.goto("http://localhost:8080/journey/index.html")
    page.screenshot(path="mobile_view.png", full_page=True)
    browser.close()
