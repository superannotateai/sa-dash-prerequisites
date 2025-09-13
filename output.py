import os
from playwright.sync_api import sync_playwright
output_dir = os.environ.get("DASH_OUTPUT_PATH", ".")
html_file_path = os.path.join(output_dir, "output.html")
png_file_path = os.path.join(output_dir, "screenshot.png")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # open a local file 
    abs_html_file_path = os.path.abspath(html_file_path)
    print(">>>>", abs_html_file_path)
    page.goto(f"file://{abs_html_file_path}")
    page.wait_for_timeout(2000)
    page.locator("#sa-chart-container").screenshot(path=png_file_path)
    
    browser.close()
