import asyncio
from playwright.async_api import async_playwright
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotus_imobiliaria.settings')
django.setup()

async def main():
    """
    Navigates to the property detail page for Imovel with ID 1,
    takes a screenshot, and saves it as 'debug_screenshot.png'.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Adjust the URL to your local development server
        url = "http://127.0.0.1:8000/imoveis/1/"

        try:
            print(f"Navigating to {url}...")
            await page.goto(url, wait_until="networkidle")

            # Take a screenshot of the full page
            screenshot_path = "debug_screenshot.png"
            await page.screenshot(path=screenshot_path, full_page=True)

            print(f"Screenshot saved to {screenshot_path}")
            print("Please view the screenshot to assess the layout.")

        except Exception as e:
            print(f"An error occurred: {e}")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
