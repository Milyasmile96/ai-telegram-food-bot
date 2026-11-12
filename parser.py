import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state="state.json")
        page = await context.new_page()
        
        print("Заходим на Яндекс.Еду...")
        await page.goto("https://eda.yandex.ru/", timeout=60000)
        await page.wait_for_timeout(5000) 
        
        print("Ищем поле поиска и вводим 'пицца'...")
        search_input = page.locator("input").first
        
        if await search_input.is_visible():
            await search_input.fill("пицца")
            await search_input.press("Enter")
            await page.wait_for_timeout(7000) 
            
            cards = await page.query_selector_all("div[data-testid='product-card'], div[class*='Card']")
            print(f"Нашли карточек: {len(cards)}. Выводим названия первых 5:\n")
            
            for i, card in enumerate(cards[:5]):
                text = await card.inner_text()
                # Разбиваем текст на строки и убираем пустые
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                
                title = "Неизвестно"
                # Ищем строку, которая не содержит цену, вес или время
                for line in lines:
                    if "₽" not in line and " г" not in line and "мин" not in line and len(line) > 3:
                        title = line
                        break
                        
                print(f"{i+1}. {title}")
        else:
            print("Поле поиска не найдено.")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())