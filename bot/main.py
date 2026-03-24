"""
Telegram-бот для трейдерских чатов.

Функции:
  1. Команды: /start, /help, /news, /setchat
  2. Фоновый парсер: каждые N минут скачивает RSS, ML-классифицирует новости и сохраняет в БД.
  3. /news → меню категорий → список новостей кнопками → OpenAI-пересказ при клике.
  4. Модерация: перехватывает сообщения в группах и применяет правила из БД.

Запуск: python -m bot.main
"""

import asyncio
import logging
import os
import re

from openai import AsyncOpenAI
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database import SessionLocal
from app import models, crud

load_dotenv()

BOT_TOKEN  = os.getenv("BOT_TOKEN")
CHAT_ID    = os.getenv("CHAT_ID", "")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")

# ── OpenAI клиент (lazy-инициализация) ────────────────────────────────────────
_openai_client: AsyncOpenAI | None = None


def get_openai() -> AsyncOpenAI | None:
    global _openai_client
    if not OPENAI_KEY:
        return None
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=OPENAI_KEY)
    return _openai_client


# ── Настройки логирования ──────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

bot    = Bot(token=BOT_TOKEN)
dp     = Dispatcher()
router = Router()
dp.include_router(router)

# Эмодзи для каждой категории
CATEGORY_EMOJI = {
    "Криптовалюты":   "₿",
    "Акции":          "📈",
    "Экономика":      "🏦",
    "Политика":       "🏛️",
    "Валютный рынок": "💱",
    "Сырьевые рынки": "🛢️",
    "Общее":          "📰",
}


# ══════════════════════════════════════════════════════════════════════════════
# КОМАНДЫ
# ══════════════════════════════════════════════════════════════════════════════

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "📈 <b>Trader News Bot</b>\n\n"
        "Я агрегирую финансовые новости из RSS-источников, "
        "классифицирую их по тематике с помощью ML и генерирую краткий пересказ через AI.\n\n"
        "Также слежу за порядком в группах — удаляю спам и рекламу.\n\n"
        "<b>Команды:</b>\n"
        "  /news — выбрать категорию и читать новости\n"
        "  /setchat — узнать ID этого чата\n"
        "  /help — справка",
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "<b>Справка по командам:</b>\n\n"
        "/start — приветствие\n"
        "/news — выбрать категорию новостей\n"
        "/setchat — показать ID текущего чата\n"
        "/help — эта справка\n\n"
        "<b>В группах:</b>\n"
        "Бот автоматически удаляет сообщения, нарушающие правила.\n"
        "Правила настраиваются в <b>Веб-админке</b>.",
        parse_mode="HTML",
    )


@router.message(Command("setchat"))
async def cmd_setchat(message: Message):
    chat_id = message.chat.id
    await message.answer(
        f"✅ ID этого чата: <code>{chat_id}</code>\n\n"
        f"Вставьте в файл <code>.env</code>:\n"
        f"<pre>CHAT_ID={chat_id}</pre>",
        parse_mode="HTML",
    )


# ══════════════════════════════════════════════════════════════════════════════
# МЕНЮ НОВОСТЕЙ (inline-клавиатура)
# ══════════════════════════════════════════════════════════════════════════════

@router.message(Command("news"))
async def cmd_news(message: Message):
    """Показывает меню выбора категории."""
    await message.answer(
        "📰 <b>Выбери интересующую тебя категорию:</b>",
        parse_mode="HTML",
        reply_markup=_category_keyboard(),
    )


def _category_keyboard() -> InlineKeyboardMarkup:
    """Строит инлайн-клавиатуру со всеми категориями."""
    builder = InlineKeyboardBuilder()
    for category, emoji in CATEGORY_EMOJI.items():
        builder.button(
            text=f"{emoji} {category}",
            callback_data=f"cat:{category}",
        )
    builder.adjust(2)
    return builder.as_markup()


@router.callback_query(F.data == "back:menu")
async def on_back_to_menu(callback: CallbackQuery):
    """Возвращает к меню выбора категорий."""
    await callback.message.edit_text(
        "📰 <b>Выбери интересующую тебя категорию:</b>",
        parse_mode="HTML",
        reply_markup=_category_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cat:"))
async def on_category_selected(callback: CallbackQuery):
    """Показывает до 5 новостей выбранной категории в виде кнопок."""
    category = callback.data.removeprefix("cat:")
    emoji = CATEGORY_EMOJI.get(category, "📰")

    db = SessionLocal()
    try:
        items = (
            db.query(models.NewsItem)
            .filter(models.NewsItem.category == category)
            .order_by(models.NewsItem.fetched_at.desc())
            .limit(5)
            .all()
        )
    finally:
        db.close()

    builder = InlineKeyboardBuilder()

    if not items:
        builder.button(text="◀️ Назад", callback_data="back:menu")
        await callback.message.edit_text(
            f"{emoji} <b>{category}</b>\n\n"
            "Новостей по этой теме пока нет.\n"
            "Добавьте RSS-источники и дождитесь парсинга.",
            parse_mode="HTML",
            reply_markup=builder.as_markup(),
        )
        await callback.answer()
        return

    # Кнопки с заголовками новостей (обрезаются до 60 символов)
    for item in items:
        title_short = (item.title[:60] + "...") if len(item.title) > 60 else item.title
        builder.button(text=title_short, callback_data=f"nw:{item.id}")
    builder.adjust(1)
    builder.button(text="◀️ Назад", callback_data="back:menu")

    await callback.message.edit_text(
        f"{emoji} <b>{category}</b> — выбери новость:",
        parse_mode="HTML",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("nw:"))
async def on_news_detail(callback: CallbackQuery):
    """Показывает подробности новости с AI-пересказом через OpenAI."""
    news_id = int(callback.data.removeprefix("nw:"))

    db = SessionLocal()
    try:
        item = db.query(models.NewsItem).filter(models.NewsItem.id == news_id).first()
    finally:
        db.close()

    if not item:
        await callback.answer("Новость не найдена.", show_alert=True)
        return

    # Кнопка «Назад» → возвращает в список новостей категории
    back_cat = item.category if item.category else "Общее"
    back_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data=f"cat:{back_cat}")]]
    )

    # Показываем «Генерирую…» пока OpenAI отвечает
    await callback.message.edit_text(
        "⏳ <i>Генерирую пересказ...</i>",
        parse_mode="HTML",
        reply_markup=back_kb,
    )
    await callback.answer()

    # Формируем текст для суммаризации
    source_text = item.title
    if item.content:
        source_text += "\n\n" + item.content

    summary = await _summarize(source_text)

    cat   = item.category if item.category else "Общее"
    emoji = CATEGORY_EMOJI.get(cat, "📰")
    src   = item.source_name if item.source_name else "—"

    text = (
        f"<b>Категория:</b> {emoji} {cat}\n\n"
        f"<b>Заголовок:</b> {item.title}\n\n"
        f"<b>Пересказ:</b>\n{summary}\n\n"
        f"<b>Источник:</b> {src}\n"
        f"<a href='{item.url}'>🔗 Читать полностью →</a>"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=back_kb,
    )


# ══════════════════════════════════════════════════════════════════════════════
# OPENAI СУММАРИЗАЦИЯ
# ══════════════════════════════════════════════════════════════════════════════

async def _summarize(text: str) -> str:
    """
    Запрашивает краткий пересказ у OpenAI gpt-4o-mini.
    Если ключ не задан или запрос упал — возвращает исходный текст.
    """
    client = get_openai()
    if not client:
        return (
            "<i>Суммаризация недоступна (OPENAI_API_KEY не задан).</i>\n\n"
            + text[:400]
        )
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты делаешь краткий пересказ финансовой новости.\n"
                        "Сохраняй только ключевые факты.\n"
                        "Не добавляй информацию, которой нет в тексте.\n"
                        "Ответ дай на русском языке.\n"
                        "Формат:\n"
                        "1. Краткий заголовок\n"
                        "2. 2–3 предложения сути новости"
                    ),
                },
                {"role": "user", "content": text[:3000]},
            ],
            max_tokens=300,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        log.error(f"[OpenAI] Ошибка: {e}")
        return f"<i>(Ошибка суммаризации)</i>\n\n{text[:400]}"


# ══════════════════════════════════════════════════════════════════════════════
# МОДЕРАЦИЯ В ГРУППОВЫХ ЧАТАХ
# ══════════════════════════════════════════════════════════════════════════════

@router.message(F.chat.type.in_({"group", "supergroup"}))
async def moderate_message(message: Message):
    """
    Перехватывает все сообщения в группах и проверяет по правилам из БД.
    Бот должен быть администратором группы с правом удалять сообщения.
    """
    text = message.text or message.caption or ""
    if not text:
        return

    db = SessionLocal()
    try:
        rules = crud.get_rules(db)
        for rule in rules:
            matched = False
            try:
                if rule.type == "keyword":
                    matched = rule.pattern.lower() in text.lower()
                elif rule.type == "regex":
                    matched = bool(re.search(rule.pattern, text, re.IGNORECASE))
                elif rule.type == "link":
                    matched = rule.pattern.lower() in text.lower()
            except re.error:
                continue

            if matched:
                log.info(f"[Mod] Правило [{rule.type}] '{rule.pattern}' → {rule.action}")

                if rule.action == "delete":
                    try:
                        await message.delete()
                    except Exception:
                        pass

                elif rule.action == "warn":
                    try:
                        await message.delete()
                    except Exception:
                        pass
                    name = message.from_user.username or message.from_user.first_name
                    await bot.send_message(
                        message.chat.id,
                        f"⚠️ @{name}, ваше сообщение удалено как нарушение правил чата.",
                    )

                elif rule.action == "ban":
                    try:
                        await message.delete()
                        await bot.ban_chat_member(message.chat.id, message.from_user.id)
                        await bot.send_message(
                            message.chat.id,
                            f"🚫 Пользователь {message.from_user.first_name} заблокирован за нарушение правил.",
                        )
                    except Exception as e:
                        log.warning(f"[Mod] Не удалось забанить: {e}")

                break
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# ФОНОВЫЙ ПАРСЕР
# ══════════════════════════════════════════════════════════════════════════════

async def fetch_news_only():
    """
    Запускается планировщиком. Парсит RSS, ML-классифицирует, сохраняет в БД.
    Автопубликация в чат отключена — новости доступны только по /news.
    """
    try:
        from parser.rss_parser import parse_all_sources
        new_items = parse_all_sources(limit_per_source=5)
        if new_items:
            log.info(f"[Scheduler] Добавлено в БД: {len(new_items)} новостей.")
    except Exception as e:
        log.error(f"[Scheduler] Ошибка парсинга: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# ЗАПУСК
# ══════════════════════════════════════════════════════════════════════════════

async def main():
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(fetch_news_only, "interval", minutes=1, id="rss_parser")
    scheduler.start()

    log.info("Бот запущен!")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
