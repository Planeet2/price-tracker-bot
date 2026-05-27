import asyncio
import html

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.config import settings
from app.database import (
    deactivate_product,
    get_products_with_latest_price,
    init_db,
    set_target_price,
    upsert_product,
)
from app.monitor import check_one_product, run_cycle
from app.scraper import scrape_product

bot = Bot(token=settings.bot_token)
dp = Dispatcher(storage=MemoryStorage())


class AddProductState(StatesGroup):
    waiting_for_url = State()
    waiting_for_target_price = State()


class TargetPriceState(StatesGroup):
    waiting_for_price = State()


def format_price(value) -> str:
    if value is None:
        return "нет данных"
    return f"{int(value):,} ₽".replace(",", " ")


def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить товар")],
            [KeyboardButton(text="📦 Мои товары"), KeyboardButton(text="🔍 Проверить цены")],
            [KeyboardButton(text="❓ Помощь")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери действие",
    )


def product_card_keyboard(product_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎯 Изменить цель", callback_data=f"target:{product_id}")],
            [InlineKeyboardButton(text="🗑 Отключить", callback_data=f"remove:{product_id}")],
        ]
    )


def skip_target_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭ Без целевой цены", callback_data="skip_target")],
        ]
    )


def remove_confirm_keyboard(product_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, отключить", callback_data=f"remove_yes:{product_id}"),
                InlineKeyboardButton(text="↩️ Отмена", callback_data="remove_no"),
            ]
        ]
    )


async def show_help(message: types.Message):
    text = (
        "👋 <b>Price Monitor</b>\n\n"
        "Теперь можно управлять ботом кнопками.\n\n"
        "<b>Что умеет бот:</b>\n"
        "➕ Добавить товар — отправляешь ссылку на товар\n"
        "📦 Мои товары — показывает список товаров\n"
        "🎯 Изменить цель — установить желаемую цену\n"
        "🗑 Отключить — убрать товар из мониторинга\n"
        "🔍 Проверить цены — запустить проверку вручную\n\n"
        "Команды тоже остались: /add, /list, /remove, /target, /check"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=main_keyboard())


async def show_products(message: types.Message):
    products = await asyncio.to_thread(get_products_with_latest_price)
    if not products:
        await message.answer(
            "📭 Список пуст. Нажми «➕ Добавить товар» и отправь ссылку.",
            reply_markup=main_keyboard(),
        )
        return

    await message.answer("📦 <b>Твои товары:</b>", parse_mode="HTML", reply_markup=main_keyboard())

    for product in products:
        name = html.escape(product["name"][:90])
        price = format_price(product["price"])
        target = format_price(product["target_price"])
        text = (
            f"#{product['id']} — <b>{name}</b>\n\n"
            f"💰 Цена сейчас: <b>{price}</b>\n"
            f"🎯 Целевая цена: <b>{target}</b>"
        )
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=product_card_keyboard(product["id"]),
        )


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await show_help(message)


@dp.message(Command("help"))
@dp.message(F.text == "❓ Помощь")
async def cmd_help(message: types.Message):
    await show_help(message)


@dp.message(Command("list"))
@dp.message(F.text == "📦 Мои товары")
async def cmd_list(message: types.Message):
    await show_products(message)


@dp.message(Command("add"))
async def cmd_add(message: types.Message, state: FSMContext):
    args = message.text.split(maxsplit=2)
    if len(args) >= 2:
        url = args[1].strip()
        target_price = int(args[2]) if len(args) == 3 and args[2].isdigit() else None
        await add_product_by_url(message, state, url, target_price)
        return

    await state.set_state(AddProductState.waiting_for_url)
    await message.answer("Пришли ссылку на товар из Citilink:", reply_markup=main_keyboard())


@dp.message(F.text == "➕ Добавить товар")
async def add_product_button(message: types.Message, state: FSMContext):
    await state.set_state(AddProductState.waiting_for_url)
    await message.answer("Пришли ссылку на товар из Citilink:", reply_markup=main_keyboard())


@dp.message(AddProductState.waiting_for_url)
async def process_product_url(message: types.Message, state: FSMContext):
    url = (message.text or "").strip()
    if not url.startswith("http"):
        await message.answer("Похоже, это не ссылка. Пришли URL товара, который начинается с http.")
        return

    await add_product_by_url(message, state, url)


async def add_product_by_url(
    message: types.Message,
    state: FSMContext,
    url: str,
    target_price: int | None = None,
):
    await message.answer("⏳ Загружаю товар и цену...")

    try:
        product = await asyncio.to_thread(scrape_product, url)
        product_id = await asyncio.to_thread(
            upsert_product,
            product.external_id,
            product.name,
            product.url,
            target_price,
        )

        await asyncio.to_thread(check_one_product, url, target_price)

        await state.update_data(product_id=product_id, url=url)

        text = (
            "✅ <b>Товар добавлен</b>\n\n"
            f"#{product_id} — <b>{html.escape(product.name)}</b>\n"
            f"💰 Цена сейчас: <b>{format_price(product.price)}</b>"
        )

        if target_price is not None:
            text += f"\n🎯 Целевая цена: <b>{format_price(target_price)}</b>"
            await state.clear()
            await message.answer(text, parse_mode="HTML", reply_markup=main_keyboard())
            return

        await state.set_state(AddProductState.waiting_for_target_price)
        await message.answer(
            text + "\n\nТеперь можешь отправить целевую цену числом, например 75000.",
            parse_mode="HTML",
            reply_markup=skip_target_keyboard(),
        )

    except Exception as exc:
        await state.clear()
        await message.answer(
            f"❌ Не удалось добавить товар: {html.escape(str(exc))}",
            parse_mode="HTML",
            reply_markup=main_keyboard(),
        )


@dp.message(AddProductState.waiting_for_target_price)
async def process_target_after_add(message: types.Message, state: FSMContext):
    price_text = (message.text or "").replace(" ", "").strip()
    if not price_text.isdigit():
        await message.answer("Пришли цену числом, например 75000, или нажми «Без целевой цены».")
        return

    data = await state.get_data()
    product_id = data.get("product_id")

    ok = await asyncio.to_thread(set_target_price, int(product_id), int(price_text))
    await state.clear()

    await message.answer(
        "✅ Целевая цена установлена" if ok else "❌ Товар не найден",
        reply_markup=main_keyboard(),
    )


@dp.callback_query(F.data == "skip_target")
async def skip_target(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Ок, товар будет отслеживаться без целевой цены.", reply_markup=main_keyboard())
    await callback.answer()


@dp.callback_query(F.data.startswith("target:"))
async def target_from_button(callback: types.CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split(":", 1)[1])
    await state.update_data(product_id=product_id)
    await state.set_state(TargetPriceState.waiting_for_price)
    await callback.message.answer(f"Введи новую целевую цену для товара #{product_id}, например 75000:")
    await callback.answer()


@dp.message(Command("target"))
async def cmd_target(message: types.Message):
    args = message.text.split()
    if len(args) != 3 or not args[1].isdigit() or not args[2].isdigit():
        await message.answer("Использование: /target <id> <цена>")
        return

    ok = await asyncio.to_thread(set_target_price, int(args[1]), int(args[2]))
    await message.answer("✅ Целевая цена обновлена" if ok else "❌ Товар не найден", reply_markup=main_keyboard())


@dp.message(TargetPriceState.waiting_for_price)
async def process_target_price(message: types.Message, state: FSMContext):
    price_text = (message.text or "").replace(" ", "").strip()
    if not price_text.isdigit():
        await message.answer("Цена должна быть числом. Например: 75000")
        return

    data = await state.get_data()
    product_id = data.get("product_id")

    ok = await asyncio.to_thread(set_target_price, int(product_id), int(price_text))
    await state.clear()

    await message.answer(
        "✅ Целевая цена обновлена" if ok else "❌ Товар не найден",
        reply_markup=main_keyboard(),
    )


@dp.callback_query(F.data.startswith("remove:"))
async def remove_from_button(callback: types.CallbackQuery):
    product_id = int(callback.data.split(":", 1)[1])
    await callback.message.answer(
        f"Точно отключить товар #{product_id} из мониторинга?",
        reply_markup=remove_confirm_keyboard(product_id),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("remove_yes:"))
async def remove_confirmed(callback: types.CallbackQuery):
    product_id = int(callback.data.split(":", 1)[1])
    ok = await asyncio.to_thread(deactivate_product, product_id)
    await callback.message.answer("✅ Товар отключён" if ok else "❌ Товар не найден", reply_markup=main_keyboard())
    await callback.answer()


@dp.callback_query(F.data == "remove_no")
async def remove_cancelled(callback: types.CallbackQuery):
    await callback.message.answer("Ок, товар оставлен в мониторинге.", reply_markup=main_keyboard())
    await callback.answer()


@dp.message(Command("remove"))
async def cmd_remove(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("Использование: /remove <id>")
        return

    ok = await asyncio.to_thread(deactivate_product, int(args[1]))
    await message.answer("✅ Товар отключён" if ok else "❌ Товар не найден", reply_markup=main_keyboard())


@dp.message(Command("check"))
@dp.message(F.text == "🔍 Проверить цены")
async def cmd_check(message: types.Message):
    await message.answer("🔍 Проверяю цены...")
    await asyncio.to_thread(run_cycle)
    await message.answer("✅ Проверка завершена", reply_markup=main_keyboard())


async def main():
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN не указан в .env")
    init_db()
    print("Telegram-бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
