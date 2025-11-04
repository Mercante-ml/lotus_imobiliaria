import asyncio
from playwright.async_api import async_playwright
import os
import django
import subprocess
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotus_imobiliaria.settings')
django.setup()

async def main():
    # Inicia o servidor Django em background em uma nova porta
    server_process = subprocess.Popen(['python', 'manage.py', 'runserver', '8001'])
    print("Servidor Django iniciado na porta 8001...")
    time.sleep(5)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        url = "http://127.0.0.1:8001/imoveis/1/"
        screenshot_path = "screenshot_lightbox.png"

        try:
            print(f"Navegando para {url}...")
            await page.goto(url, wait_until="networkidle")

            gallery_selector = "#gallery-detalhe a"
            print(f"Clicando na primeira imagem da galeria ('{gallery_selector}')...")
            await page.locator(gallery_selector).first.click()

            lightbox_selector = ".pswp"
            print(f"Aguardando pelo seletor do lightbox ('{lightbox_selector}')...")
            await page.wait_for_selector(lightbox_selector, state="visible", timeout=5000)

            print("Lightbox detectado! Tirando screenshot...")
            await page.screenshot(path=screenshot_path, full_page=True)

            print(f"SUCESSO: O lightbox parece ter aberto corretamente. Verifique o arquivo '{screenshot_path}'")

        except Exception as e:
            print(f"FALHA: Ocorreu um erro ao tentar verificar o lightbox: {e}")
            await page.screenshot(path="screenshot_falha.png", full_page=True)
            print("Um screenshot de depuração foi salvo como 'screenshot_falha.png'")

        finally:
            await browser.close()
            server_process.kill()
            print("Servidor Django parado.")

if __name__ == "__main__":
    asyncio.run(main())
