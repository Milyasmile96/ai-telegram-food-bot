import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # Запускаем браузер (headless=False означает, что мы увидим окно)
        browser = await p.chromium.launch(headless=False) 
        page = await browser.new_page()
        
        print("Открываем Яндекс.Еду...")
        # Ждем загрузки сайта
        await page.goto("https://eda.yandex.ru/", timeout=60000)
        
        # Ждем 5 секунд, чтобы сайт прогрузился
        await page.wait_for_timeout(5000)
        
        # Делаем скриншот
        await page.screenshot(path="eda_screen.png")
        print("Скриншот сохранен как eda_screen.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())