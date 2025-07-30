import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram import Router
from aiogram.client.default import DefaultBotProperties
from aiogram .types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.main import main_menu
from catalog.data import catalog_items
from keyboards.catalog import get_catalog_keyboard
from uuid import uuid4
from catalog.db import init_db, add_item, get_all_items
from catalog.db import delete_item, update_item, update_item_field
from keyboards.admin import get_admin_item_keyboard, get_edit_field_keyboard
from config import API_TOKEN, ADMIN_IDS


bot = Bot(token=API_TOKEN)

router = Router()
user_cart = {}


@router.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer("Привет! Добро пожаловать в магазин художницы \n\n Выберите действие:",
                         reply_markup=main_menu)


async def main():
    bot = Bot(
        token=API_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    init_db()
    await dp.start_polling(bot)


# @router.message(F.text == "Каталог")
# async def show_catalog(message: Message):
    # await message.answer("Пока каталог пуст. В ближайшее время здесь появятся товары!")


@router.message(F.text == "👩‍🎨 О художнице")
async def about_artist(message: Message):
    await message.answer("""Мультидисциплинарная художница и исследовательница. Интересуюсь темами натурфилософии, коммуникации
человека и природы, пограничными, трансгрессивными и трансцендентными опытами в культуре человеческого и нечеловеческого, явлениями, ускользающими от человеческого глаза. В данный период сфокусирована на работе с графикой, живописью, иллюстрацией.
\n
мой профиль на BIZAR - https://bizar.art/author/katya-lesun-bb8r
моя коллаборация с BEFREE - https://collab.befree.ru/katya_lesun""")


@router.message(F.text == "📱 Контакты")
async def show_contacts(message: Message):
    await message.answer("Связаться со мной можно через Telegram: @katyalesun\nИли по e-mail: katyalesunstudio@gmail.com")


# @router.message(F.text == "Каталог")
# async def show_catalog(message: Message):
    # for item in catalog_items:
       # await message.answer_photo(
           # photo=item["photo"],
           # caption=f"<b>{item['title']}</b>\n\n{item['description']}\n\nЦена: <b>{item['price']}</b>",
           # reply_markup=get_catalog_keyboard(item["id"])
        #)

@router.message(F.text == "🎨 Каталог")
async def show_catalog(message: Message):
    items = get_all_items()
    if not items:
        await message.answer("Пока каталог пуст. Добавьте товары через /add")
        return

    for item in items:
        await message.answer_photo(
            photo=item["photo"],
            caption=f"<b>{item['title']}</b>\n\n{item['description']}\n\nЦена: <b>{item['price']}</b>",
            reply_markup=get_catalog_keyboard(item["id"])
        )


@router.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback: CallbackQuery):
    item_id = callback.data.split("_")[1]
    user_id = callback.from_user.id

    item = next((item for item in get_all_items() if item["id"] == item_id), None)
    if item is None:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return

    user_cart.setdefault(user_id, []).append(item)
    await callback.answer(f"✅ Добавлено: {item['title']}")


@router.message(F.text == "🛒 Корзина")
async def show_cart(message: Message):
    user_id = message.from_user.id
    cart = user_cart.get(user_id, [])

    if not cart:
        await message.answer("🧺 Ваша корзина пуста.")
        return

    text = "<b>🧺 Ваша корзина:</b>\n\n"
    total = 0

    for item in cart:
        text += f"• {item['title']} — {item['price']}\n"
        total += int(item['price'].replace("₽", "").strip())

    text += f"\n<b>Итого:</b> {total}₽"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Очистить", callback_data="clear_cart")],
        [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")]
    ])

    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_cart[user_id] = []
    await callback.message.edit_text("🧺 Корзина очищена.")
    await callback.answer()


# @router.callback_query(F.data == "checkout")
# async def checkout(callback: CallbackQuery):
    # await callback.message.edit_text("✅ Заказ оформлен! Мы свяжемся с вами в ближайшее время.")
    # user_cart[callback.from_user.id] = []
    # await callback.answer()

class OrderStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()


@router.callback_query(F.data == "checkout")
async def checkout(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📛 Пожалуйста, введите ваше имя:")
    await state.set_state(OrderStates.waiting_for_name)
    await callback.answer()


@router.message(OrderStates.waiting_for_name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📞 Теперь введите ваш номер телефона:")
    await state.set_state(OrderStates.waiting_for_phone)


@router.message(OrderStates.waiting_for_phone)
async def get_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    data = await state.get_data()

    user_id = message.from_user.id
    cart = user_cart.get(user_id, [])

    # Формируем текст заказа
    text = f"✅ Спасибо за заказ, {data['name']}!\n\n"
    text += "🧺 Ваш заказ:\n"
    for item in cart:
        text += f"• {item['title']} — {item['price']}\n"
    total = sum(int(item['price'].replace("₽", "").strip()) for item in cart)
    text += f"\n📞 Телефон: {data['phone']}\n"
    text += f"💰 Итого: {total}₽"

    await message.answer(text)
    await state.clear()
    user_cart[user_id] = []  # Очищаем корзину


class AddArtwork(StatesGroup):
    waiting_for_photo = State()
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_price = State()


@router.message(F.text == "/admin")
async def admin_panel(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("🚫 У вас нет доступа к админке.")
        return

    kb = types.ReplyKeyboardMarkup(keyboard=[
        [types.KeyboardButton(text="/add")],
        [types.KeyboardButton(text="Назад в меню")]
    ], resize_keyboard=True)

    await message.answer("🔧 Админ-панель:\n\n- Нажмите /add чтобы добавить товар.",
                         reply_markup=kb)


@router.message(F.text == "/add")
async def start_add_artwork(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет прав для добавления товаров.")
        return
    await message.answer("🖼️ Отправьте фото картины:")
    await state.set_state(AddArtwork.waiting_for_photo)


@router.message(AddArtwork.waiting_for_photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    photo = message.photo[-1].file_id
    await state.update_data(photo=photo)
    await message.answer("✏️ Введите название картины:")
    await state.set_state(AddArtwork.waiting_for_title)


@router.message(AddArtwork.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("📝 Введите описание:")
    await state.set_state(AddArtwork.waiting_for_description)


@router.message(AddArtwork.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("💰 Введите цену (например: 2500₽):")
    await state.set_state(AddArtwork.waiting_for_price)


@router.message(AddArtwork.waiting_for_price)
async def process_price(message: Message, state: FSMContext):
    data = await state.update_data(price=message.text)

    new_item = {
        "id": str(uuid4()),  # генерируем уникальный ID
        "title": data["title"],
        "description": data["description"],
        "price": data["price"],
        "photo": data["photo"]
    }

    add_item(new_item)  # ⬅ сохраняем в базу данных (функция из db.py)

    await message.answer("✅ Картина добавлена в каталог!")
    await state.clear()


@router.message(F.text == "/admin_catalog")
async def admin_catalog(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ Нет доступа.")
        return

    items = get_all_items()
    if not items:
        await message.answer("📭 Каталог пуст.")
        return

    for item in items:
        await message.answer_photo(
            photo=item["photo"],
            caption=f"<b>{item['title']}</b>\n\n{item['description']}\nЦена: <b>{item['price']}</b>",
            reply_markup=get_admin_item_keyboard(item["id"]),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("delete_"))
async def handle_delete(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Нет прав", show_alert=True)
        return

    item_id = callback.data.split("_")[1]
    delete_item(item_id)

    await callback.message.edit_caption("🗑️ Товар удалён.")
    await callback.answer("Удалено")


class EditArtwork(StatesGroup):
    waiting_for_photo = State()
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_price = State()


@router.callback_query(F.data.startswith("edit_"))
async def choose_edit_field(callback: CallbackQuery):
    item_id = callback.data.split("_")[1]
    kb = get_edit_field_keyboard(item_id)  # Клавиатура с кнопками: editphoto_<id>, edittitle_<id> и т.д.
    await callback.message.answer("Что вы хотите изменить?", reply_markup=kb)
    await callback.answer()


@router.message(EditArtwork.waiting_for_photo, F.photo)
async def edit_photo(message: Message, state: FSMContext):
    photo = message.photo[-1].file_id
    await state.update_data(photo=photo)
    await message.answer("✏️ Введите новое название:")
    await state.set_state(EditArtwork.waiting_for_title)


@router.message(EditArtwork.waiting_for_title)
async def edit_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("📝 Введите новое описание:")
    await state.set_state(EditArtwork.waiting_for_description)


@router.message(EditArtwork.waiting_for_description)
async def edit_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("💰 Введите новую цену (например: 2500₽):")
    await state.set_state(EditArtwork.waiting_for_price)


@router.message(EditArtwork.waiting_for_price)
async def edit_price(message: Message, state: FSMContext):
    data = await state.update_data(price=message.text)

    updated_item = {
        "id": data["id"],
        "photo": data["photo"],
        "title": data["title"],
        "description": data["description"],
        "price": data["price"]
    }

    update_item(updated_item)  # см. шаг 5

    await message.answer("✅ Товар обновлён!")
    await state.clear()


@router.callback_query(F.data.startswith("choose_edit_"))
async def choose_edit_field(callback: CallbackQuery):
    item_id = callback.data.split("_")[2]
    await callback.message.answer("Что вы хотите изменить?", reply_markup=get_edit_field_keyboard(item_id))
    await callback.answer()


class EditField(StatesGroup):
    editing_photo = State()
    editing_title = State()
    editing_description = State()
    editing_price = State()


@router.callback_query(F.data.startswith("editphoto_"))
async def ask_new_photo(callback: CallbackQuery, state: FSMContext):
    item_id = callback.data.split("_")[1]
    await state.update_data(id=item_id)
    await callback.message.answer("📸 Отправьте новое фото:")
    await state.set_state(EditField.editing_photo)
    await callback.answer()


@router.message(EditField.editing_photo, F.photo)
async def save_new_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    new_photo = message.photo[-1].file_id
    update_item_field(data["id"], "photo", new_photo)
    await message.answer("✅ Фото обновлено!")
    await state.clear()


@router.callback_query(F.data.startswith("edittitle_"))
async def ask_new_title(callback: CallbackQuery, state: FSMContext):
    item_id = callback.data.split("_")[1]
    await state.update_data(id=item_id)
    await callback.message.answer("✏️ Введите новое название:")
    await state.set_state(EditField.editing_title)
    await callback.answer()


@router.message(EditField.editing_title)
async def save_new_title(message: Message, state: FSMContext):
    data = await state.get_data()
    update_item_field(data["id"], "title", message.text)
    await message.answer("✅ Название обновлено!")
    await state.clear()


@router.callback_query(F.data.startswith("editdesc_"))
async def ask_new_description(callback: CallbackQuery, state: FSMContext):
    item_id = callback.data.split("_")[1]
    await state.update_data(id=item_id)
    await callback.message.answer("📝 Введите новое описание:")
    await state.set_state(EditField.editing_description)
    await callback.answer()


@router.message(EditField.editing_description)
async def save_new_description(message: Message, state: FSMContext):
    data = await state.get_data()
    update_item_field(data["id"], "description", message.text)
    await message.answer("✅ Описание обновлено!")
    await state.clear()


@router.callback_query(F.data.startswith("editprice_"))
async def ask_new_price(callback: CallbackQuery, state: FSMContext):
    item_id = callback.data.split("_")[1]
    await state.update_data(id=item_id)
    await callback.message.answer("💰 Введите новую цену:")
    await state.set_state(EditField.editing_price)
    await callback.answer()


@router.message(EditField.editing_price)
async def save_new_price(message: Message, state: FSMContext):
    data = await state.get_data()
    update_item_field(data["id"], "price", message.text)
    await message.answer("✅ Цена обновлена!")
    await state.clear()


if __name__ == "__main__":
    asyncio.run(main())
