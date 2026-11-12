import asyncio
import os
import uuid
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from playwright.async_api import async_playwright
from openai import OpenAI

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
dp = Dispatcher()

CHAT_HISTORY = {}
SESSIONS = {}

async def get_search_query(chat_id):
    history = CHAT_HISTORY.get(chat_id, [])[-6:]
    messages = [
        {"role": "system", "content": "Ты эксперт по еде. Переведи запрос пользователя в КОНКРЕТНОЕ блюдо для поиска (например: 'стейк', 'рыба', 'салат', 'курица'). НЕ возвращай слова 'ужин', 'обед', 'без глютена'. Верни ТОЛЬКО 1-2 слова."}
    ] + history
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages
    )
    return response.choices[0].message.content.strip().lower()

async def get_food_from_yandex(query):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True) 
        context = await browser.new_context(storage_state="state.json")
        page = await context.new_page()
        
        try:
            # Просто заходим на главную и ищем. Самый стабильный метод.
            await page.goto("https://eda.yandex.ru/", timeout=60000)
            await page.wait_for_timeout(5000)
            
            search_input = page.locator("input").first
            await search_input.fill(query)
            await search_input.press("Enter")
            await page.wait_for_timeout(7000) 
            
            body_text = await page.inner_text("body")
            current_url = page.url
            
            await browser.close()
            return body_text[:15000], current_url
            
        except Exception as e:
            try:
                await browser.close()
            except:
                pass
            raise e

async def ask_ai_for_healthy_food(chat_id, raw_text, default_url, previous_context=""):
    history = CHAT_HISTORY.get(chat_id, [])
    
    prompt = f"""
    Данные с сайта:
    {raw_text}
    
    Ранее показывали (НЕ ПОВТОРЯЙ):
    {previous_context}
    
    Твоя задача:
    1. Найди 3 блюда, которые подходят под запрос пользователя.
    2. Отсортируй по рейтингу.
    3. Оформи СТРОГО по шаблону:
    
    <b>1. [Название блюда]</b>
    ⭐ Рейтинг: [Рейтинг]
    🍽️ Заведение: [Название]
    💰 Цена: [Цена]
    🔥 Калории: [Из текста]
    <i>[Краткий комментарий диетолога]</i>
    <a href="{default_url}">Открыть поиск в Яндекс.Еде</a>
    
    4. ЗАПРЕЩЕНО: использовать <br>, <h3>, <ul>, <li>, **, ###.
    """
    
    messages = [
        {"role": "system", "content": "Ты ассистент-диетолог. Строго соблюдай HTML-форматирование."}
    ] + history + [
        {"role": "user", "content": prompt}
    ]
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=0.3
    )
    return response.choices[0].message.content

def clean_text_for_telegram(text):
    text = text.replace("\\n", "\n")
    text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    text = text.replace("<h3>", "<b>").replace("</h3>", "</b>")
    text = text.replace("<ul>", "").replace("</ul>", "")
    text = text.replace("<li>", "• ").replace("</li>", "")
    text = text.replace("<p>", "").replace("</p>", "\n")
    text = text.replace("###", "").replace("**", "") 
    return text

def get_next_button(session_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Не нашел подходящее? Показать еще", callback_data=f"next:{session_id}")]
    ])
    return keyboard

@dp.message(Command("start"))
async def start(message: types.Message):
    CHAT_HISTORY[message.chat.id] = []
    await message.answer("Привет! 🥗 Я твой умный помощник по еде.\n\nНапиши, что ты хочешь съесть, и я подберу варианты.")

@dp.message()
async def handle_food(message: types.Message):
    user_text = message.text
    if not user_text: return

    chat_id = message.chat.id
    if chat_id not in CHAT_HISTORY:
        CHAT_HISTORY[chat_id] = []
    
    CHAT_HISTORY[chat_id].append({"role": "user", "content": user_text})
    if len(CHAT_HISTORY[chat_id]) > 10:
        CHAT_HISTORY[chat_id] = CHAT_HISTORY[chat_id][-10:]

    wait_msg = await message.answer("🔍 Ищу блюда и анализирую меню... Подожди 20-30 секунд.")
    
    try:
        query = await get_search_query(chat_id)
        raw_data, default_url = await get_food_from_yandex(query)
        
        if not raw_data:
            await wait_msg.edit_text("😔 Ничего не найдено. Попробуй другое блюдо.")
            return

        await wait_msg.edit_text("🧠 Диетолог выбирает лучшее...")
        
        ai_answer = await ask_ai_for_healthy_food(chat_id, raw_data, default_url)
        safe_answer = clean_text_for_telegram(ai_answer)
        
        CHAT_HISTORY[chat_id].append({"role": "assistant", "content": safe_answer})
        
        session_id = str(uuid.uuid4())[:8]
        SESSIONS[session_id] = {
            "chat_id": chat_id,
            "raw_data": raw_data,
            "url": default_url,
            "previous_context": safe_answer
        }
        
        await message.answer(safe_answer, parse_mode="HTML", disable_web_page_preview=True, reply_markup=get_next_button(session_id))
        await wait_msg.delete()
        
    except Exception as e:
        await message.answer(f"Ой, произошла ошибка: {e}")

@dp.callback_query(F.data.startswith("next:"))
async def handle_next(callback: CallbackQuery):
    session_id = callback.data.split(":")[1]
    session = SESSIONS.get(session_id)
    
    if not session:
        await callback.answer("Сессия устарела. Напишите запрос заново.")
        return
        
    await callback.answer("Ищу другие варианты...")
    await callback.message.edit_reply_markup(reply_markup=None)
    
    chat_id = session["chat_id"]
    
    try:
        ai_answer = await ask_ai_for_healthy_food(
            chat_id, 
            session["raw_data"], 
            session["url"], 
            session["previous_context"]
        )
        safe_answer = clean_text_for_telegram(ai_answer)
        
        if "Больше вариантов не найдено" in safe_answer or "не найдено" in safe_answer:
            await callback.message.answer(safe_answer)
            return

        session["previous_context"] += "\n" + safe_answer
        CHAT_HISTORY[chat_id].append({"role": "assistant", "content": safe_answer})
        
        await callback.message.answer(safe_answer, parse_mode="HTML", disable_web_page_preview=True, reply_markup=get_next_button(session_id))
        
    except Exception as e:
        await callback.message.answer(f"Ой, произошла ошибка: {e}")

async def main():
    bot = Bot(token=BOT_TOKEN)
    print("Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())