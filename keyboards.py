from telebot import types
from bot_config import CATEGORIES


def generate_get_phone_number():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton(text='Мой номер телефона', request_contact=True)
    keyboard.add(btn)
    return keyboard


def generated_main_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    basket_btn = types.KeyboardButton(text="🛒 Корзина")
    buttons = []
    for category_name in CATEGORIES.keys():
        btn = types.KeyboardButton(text=category_name)
        buttons.append(btn)
    keyboard.add(*buttons, basket_btn)
    return keyboard


def generate_details_markup(link, product_id, price, product_count=0):
    markup = types.InlineKeyboardMarkup()

    minus_btn = types.InlineKeyboardButton(text="-", callback_data=f"action_minus_{product_id}_{product_count}")
    product_count_btn = types.InlineKeyboardButton(text=str(product_count), callback_data=f"action_current-count_{product_id}_{product_count}")
    plus_btn = types.InlineKeyboardButton(text="+", callback_data=f"action_plus_{product_id}_{product_count}")

    link_button = types.InlineKeyboardButton(text='Подробнее', url=link)
    buy_button = types.InlineKeyboardButton(text='В корзину', callback_data=f"add_{product_id}_{product_count}_{price}")

    markup.add(minus_btn, product_count_btn, plus_btn)
    markup.add(buy_button, link_button)
    return markup


def generate_cart_menu(cart_id):
    keyboard = types.InlineKeyboardMarkup()
    pay_btn = types.InlineKeyboardButton(text="Оплатить", callback_data=f"pay_{cart_id}")
    keyboard.add(pay_btn)
    return keyboard


def generate_pagination(pages, current_page=1):
    keyboard = types.InlineKeyboardMarkup()
    first_btn = types.InlineKeyboardButton(text="\U000023EA", callback_data="1")

    prev_btn = types.InlineKeyboardButton(text="\U000025C0", callback_data=str(current_page - 1))
    next_btn = types.InlineKeyboardButton(text="\U000025B6", callback_data=str(current_page + 1))

    current_btn = types.InlineKeyboardButton(text=str(current_page), callback_data=str(current_page))

    last_btn = types.InlineKeyboardButton(text="\U000023E9", callback_data=str(pages))

    if 3 <= current_page < pages - 1 and pages > 4:
        keyboard.row(first_btn, prev_btn, current_btn, next_btn, last_btn)

    elif current_page == pages and pages > 2:
        keyboard.row(first_btn, prev_btn, current_btn)

    elif current_page == 1 and pages == 2:
        keyboard.row(current_btn, next)

    elif current_page == 2 and pages == 2:
        keyboard.row(prev_btn, current_btn)

    elif current_page in [2, 3] and pages <= 4:
        keyboard.row(prev_btn, current_btn, next_btn)

    elif current_page == 1 and pages > 2:
        keyboard.row(current_btn, next_btn, last_btn)

    elif current_page == 2 and pages > 4:
        keyboard.row(prev_btn, current_btn, next_btn, last_btn)

    elif current_page == pages - 1 and pages > 4:
        keyboard.row(first_btn, prev_btn, current_btn, next_btn)

    return keyboard
