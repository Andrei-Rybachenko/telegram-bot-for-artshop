from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_item_keyboard(item_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_{item_id}"),
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_{item_id}")
        ]
    ])


def get_edit_field_keyboard(item_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 Фото", callback_data=f"editphoto_{item_id}")],
        [InlineKeyboardButton(text="✏️ Название", callback_data=f"edittitle_{item_id}")],
        [InlineKeyboardButton(text="📝 Описание", callback_data=f"editdesc_{item_id}")],
        [InlineKeyboardButton(text="💰 Цена", callback_data=f"editprice_{item_id}")],
    ])
