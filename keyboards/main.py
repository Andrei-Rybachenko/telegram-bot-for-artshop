from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎨 Каталог")],
        [KeyboardButton(text="👩‍🎨 О художнице"), KeyboardButton(text="📱 Контакты")],
        [KeyboardButton(text="🛒 Корзина")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие"
)
