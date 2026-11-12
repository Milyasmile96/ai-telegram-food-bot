import asyncio
import os
from playwright.async_api import async_playwright
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Настраиваем клиент DeepSeek
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

async def get_food_from_yandex(query):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state="state.json")
        page = await context.new_page()
        
        print(f"Ищем в Яндекс.Еде: {query}...")
        await page.goto("https://eda.yandex.ru/", timeout=60000)
        await page.wait_for_timeout(5000) 
        
        search_input = page.locator("input").first
        await search_input.fill(query)
        await search_input.press("Enter")
        await page.wait_for_timeout(7000) 
        
        print("Собираем весь текст со страницы результатов...")
        body_text = await page.inner_text("body")
        
        await browser.close()
        return body_text[:10000]

async def ask_ai_for_healthy_food(query, raw_text):
    print("Отправляем данные в DeepSeek для анализа...")
    
    prompt = f"""
    Ты — профессиональный диетолог. Пользователь искал в Яндекс.Еде: "{query}".
    Вот сырой текст с карточек товаров:
    
    {raw_text}
    
    Твоя задача: выбери 2-3 самых полезных (с медицинской точки зрения) блюда из этого списка. 
    Напиши их названия и кратко объясни, почему они полезны. Если там одна сплошная пицца и бургеры, 
    выбери наименее вредные варианты и дай совет по порции.
    """
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "Ты полезный ассистент-диетолог."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    
    return response.choices[0].message.content

async def main():
    query = "пицца" 
    raw_data = await get_food_from_yandex(query)
    
    print("\n--- СЫРЫЕ ДАННЫЕ (первые 300 символов) ---")
    print(raw_data[:300] + "...")
    
    ai_answer = await ask_ai_for_healthy_food(query, raw_data)
    
    print("\n--- ОТВЕТ ИИ (ДИЕТОЛОГА) ---")
    print(ai_answer)

if __name__ == "__main__":
    asyncio.run(main())