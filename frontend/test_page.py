"""Check custom-area page for errors and take screenshot."""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # Capture console errors
    errors = []
    page.on("console", lambda msg: errors.append(f"[{msg.type}] {msg.text}") if msg.type in ("error", "warning") else None)
    page.on("pageerror", lambda err: errors.append(f"[PAGE ERROR] {err.message}"))

    print("Navigating to custom-area...")
    page.goto('http://localhost:5174/custom-area', timeout=15000)
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(3000)

    print("\n--- Console Errors/Warnings ---")
    for e in errors[:20]:
        print(e)
    if not errors:
        print("(none)")

    # Check if map container exists
    map_el = page.locator('.map-container')
    print(f"\nMap container exists: {map_el.count() > 0}")

    # Check if header renders
    header = page.locator('.app-header')
    print(f"Header exists: {header.count() > 0}")

    # Check right panel tabs
    tabs = page.locator('.tab-btn')
    print(f"Tab buttons: {tabs.count()}")

    page.screenshot(path='C:/Users/19161/Desktop/custom-area-screenshot.png', full_page=False)
    print("\nScreenshot saved to desktop. File size hint: screenshot taken.")

    browser.close()
