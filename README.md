# 🥗 AI-бот для подбора еды из Яндекс.Еды

Телеграм-бот, который автоматизирует поиск блюд в Яндекс.Еде и использует нейросеть (DeepSeek API) для выбора лучших вариантов под запрос пользователя.

## 🛠 Стек технологий:
* **Python 3.14**
* **Aiogram 3.x** (Telegram Bot API)
* **Playwright** (Web Scraping)
* **OpenAI / DeepSeek API** (LLM Integration)
* **Asyncio**

## ⚡️ Особенности:
* Понимает контекст диалога (если вы передумали, он ищет новое блюдо).
* Выдает 3 варианта блюд с ценой, рейтингом и комментарием диетолога.
* Кнопка «Показать еще» (Infinite Scroll) без повторного парсинга сайта.
* Обход блокировок с помощью сохранения Cookies (`state.json`).

## 🚀 Как запустить:
1. Установите библиотеки: `pip install aiogram playwright openai python-dotenv`
2. Установите браузер для Playwright: `playwright install chromium`
3. Создайте файл `.env` и добавьте туда `BOT_TOKEN` и `DEEPSEEK_API_KEY`.
4. Запустите бота: `python bot.py`
