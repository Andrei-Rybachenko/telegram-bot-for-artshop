from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_catalog_keyboard(item_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧺 Добавить в корзину", callback_data=f"add_{item_id}")]
    ])
