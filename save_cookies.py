import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # Запускаем браузер
        browser = await p.chromium.launch(headless=False)
        # Создаем контекст (это как отдельное окно инкогнито, где мы можем сохранять данные)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("Открываем Яндекс.Еду...")
        await page.goto("https://eda.yandex.ru/")
        
        # Ждем, пока ты сама всё настроишь
        print("\n=== ВАЖНО ===")
        print("1. В открывшемся окне браузера выбери свой адрес доставки.")
        print("2. Если нужно, авторизуйся (войди в свой аккаунт Яндекса).")
        print("3. Когда закончишь, вернись в это окно терминала и нажми Enter.")
        input("Нажми Enter здесь, когда всё настроишь в браузере...")
        
        # Сохраняем все куки и состояние сессии в файл
        await context.storage_state(path="state.json")
        print("Сессия успешно сохранена в файл state.json!")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())