import asyncio
from playwright.async_api import async_playwright
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotus_imobiliaria.settings')
django.setup()

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        url = "http://127.0.0.1:8000/sobre/"

        try:
            print(f"Navegando para {url}...")
            await page.goto(url, wait_until="networkidle")

            # Verifica se o título padrão está na página
            conteudo_titulo = await page.locator('h1').inner_text()
            assert "Página Sobre" in conteudo_titulo
            print("Teste da Página Sobre: SUCESSO - Título encontrado.")

            screenshot_path = "screenshot_sobre.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot da página 'Sobre' salvo em: {screenshot_path}")

        except Exception as e:
            print(f"Teste da Página Sobre: FALHOU - {e}")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
