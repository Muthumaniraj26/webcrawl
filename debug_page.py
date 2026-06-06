import sys
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

def debug_url(url, output_html, output_png):
    print(f"Debugging URL: {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-http2"
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        Stealth().apply_stealth_sync(page)
        
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)
            
            # Save HTML
            html = page.content()
            with open(output_html, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"Saved HTML to {output_html}")
            
            # Save Screenshot
            page.screenshot(path=output_png)
            print(f"Saved screenshot to {output_png}")
            
        except Exception as e:
            print(f"Error during debug: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    url = "https://dir.indiamart.com/search.mp?ss=Spa+Consultants&cq=Noida"
    if len(sys.argv) > 1:
        url = sys.argv[1]
    debug_url(url, "debug_output.html", "debug_screenshot.png")
