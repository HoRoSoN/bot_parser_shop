from telebot import TeleBot
from telebot.types import LabeledPrice

from parser_config import database, cursor
from keyboards import (generate_get_phone_number, generated_main_menu,
                       generate_details_markup, generate_pagination,
                       generate_cart_menu)
from bot_config import CATEGORIES, DATA, MAX_QUANTITY_PRODUCT_IN_PAGE
from utils import get_total_pages, cleaned_price

from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = TeleBot(TOKEN, parse_mode='HTML')


@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    first_name = message.from_user.first_name

    user_message = bot.send_message(chat_id,
                                    f'Привет {first_name}\nЭто тестовый бот\nЗдесь вы можете посмотреть и заказать товары!',
                                    reply_markup=generate_get_phone_number())

    cursor.execute("""SELECT *
    FROM users
    WHERE telegram_id = %s""", (chat_id,))
    user = cursor.fetchone()
    if not user:
        bot.register_next_step_handler(user_message, register_user)
    else:
        chose_category(message)


def register_user(message):
    chat_id = message.chat.id
    try:
        phone = message.contact.phone_number
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name

        cursor.execute('''INSERT INTO users(telegram_id, first_name, last_name, phone)
        VALUES(%s, %s, %s, %s)
        ON CONFLICT(telegram_id) DO NOTHING
        ''', (chat_id, first_name, last_name, phone))

        # Создание корзины под пользователя
        cursor.execute("""INSERT INTO carts (user_id)
        SELECT user_id
        FROM users
        WHERE telegram_id = %s
        ON CONFLICT(user_id) DO NOTHING
        """, (chat_id,))

        database.commit()
        chose_category(message)
    except Exception:
        bot.send_message(chat_id, "Нажмите на кнопку !!!", reply_markup=generate_get_phone_number())
        bot.register_next_step_handler(message, register_user)


def chose_category(message):
    chat_id = message.chat.id
    user_message = bot.send_message(chat_id, "Выберите категорию: ", reply_markup=generated_main_menu())
    bot.register_next_step_handler(user_message, show_category)


# Рекурсия - просто вызов одной функции несколько раз.

@bot.message_handler(regexp=r'\/product_[0-9]+')
def show_product_details(message, product_count=0, product_id=None, send_message=True):
    chat_id = message.chat.id
    # product_11
    if not product_id:
        _, product_id = message.text.split('_')
    cursor.execute(
        '''
        SELECT title, brand, price, image, link, characteristics, in_storage
        FROM products
        WHERE product_id = %s 
        ''', (product_id,)
    )
    product = cursor.fetchone()

    if product:
        title = product[0]
        brand = product[1]
        price = product[2]
        image = product[3]
        link = product[4]
        characteristics = product[5]
        in_storage = product[6]
        msg_for_user = f'''<b>{title}</b> 
<b>{brand}</b>
<b>Описание товара</b>:
<i>{characteristics}</i>
<b>Стоимость: </b>{price}
<i>На складе: {in_storage}</i>
'''
        markup = generate_details_markup(link=link, product_id=product_id, price=cleaned_price(price),
                                         product_count=product_count)
        if send_message:
            bot.send_photo(chat_id, photo=image, caption=msg_for_user, reply_markup=markup)
        else:
            bot.edit_message_reply_markup(chat_id=chat_id, message_id=message.id, reply_markup=markup)
    else:
        bot.send_message(chat_id, 'Продукт не найден')


@bot.message_handler(func=lambda message: "корзина" in message.text.lower())
def show_cart(message):
    chat_id = message.chat.id

    # Получить все продукты c одной корзины
    cursor.execute("""SELECT title, cart_products.quantity, cart_products.price
    FROM cart_products
    JOIN products USING(product_id)
    WHERE cart_id = (
        SELECT cart_id
        FROM carts
        WHERE user_id = (
            SELECT user_id 
            FROM users
            WHERE telegram_id = %s
        )
    )
    """, (chat_id,))
    products = cursor.fetchall()

    # Получение общей стоимости и общего кол-ва товаров корзины
    cursor.execute("""SELECT cart_id, total_price, total_quantity
    FROM carts
    WHERE user_id = (
        SELECT user_id 
        FROM users
        WHERE telegram_id = %s
    )""", (chat_id,))
    cart_id, total_price, total_quantity = cursor.fetchone()

    cart_text = "Ваша корзина:\n"
    i = 0
    for title, quantity, price in products:
        i += 1
        cart_text += f"""{i}.{title}
Кол-во: {quantity}
Стоимость: {price} сум\n\n"""

    cart_text += f"""<i>Общее кол-во товаров в корзине: {total_quantity}</i>
<i>Общая стоимость корзины: {total_price} сум</i>
Очистить корзину - /clear_cart"""
    bot.send_message(chat_id, cart_text, reply_markup=generate_cart_menu(cart_id))


@bot.message_handler(regexp=r'[а-яА-Яё]+')
def show_category(message):
    chat_id = message.chat.id
    category_name = message.text
    if category_name in CATEGORIES:
        category_id = CATEGORIES[category_name]["category_id"]

        cursor.execute('''
            SELECT COUNT(*)
            FROM products
            WHERE category_id = %s
        ''', (category_id,))
        DATA["count_product"] = cursor.fetchone()[0]
        DATA["total_pages"] = get_total_pages(DATA["count_product"], MAX_QUANTITY_PRODUCT_IN_PAGE)
        DATA["category_name"] = category_name

        # Получение информации о товарах
        cursor.execute("""
            SELECT product_id, title, price
            FROM products
            JOIN categories USING(category_id)
            WHERE category_id = %s
        """, (category_id,))
        # [(product_id, title, price),(product_id, title, price)]
        DATA["products"] = cursor.fetchall()

        if DATA["products"]:
            product_pagination(message)
        else:
            bot.send_message(chat_id, "Ничего не найдено")


def product_pagination(message):
    chat_id = message.chat.id
    user_text = f"Список товаров в категории {DATA['category_name']}\n\n"
    i = 1

    # ОТрисовка сообщения

    for product in DATA["products"][0:MAX_QUANTITY_PRODUCT_IN_PAGE]:
        product_id = product[0]
        title = product[1]
        price = product[2]

        user_text += f"""{i}. {title}
Стоимость: {price}
Подробнее: /product_{product_id}\n\n"""
        i += 1

    bot.send_message(chat_id, user_text, reply_markup=generate_pagination(DATA["total_pages"]))


@bot.callback_query_handler(func=lambda call: "action" in call.data)
def action_product_detail(call):
    _, action, product_id, product_count = call.data.split("_")
    cursor.execute("""
        SELECT in_storage
        FROM products
        WHERE product_id = %s
    """, (product_id,))
    in_storage = cursor.fetchone()[0]

    if action == "current-count":
        return bot.answer_callback_query(call.id, "Количество выбранных товаров")
    elif action == "plus" and int(product_count) < in_storage:
        product_count = int(product_count) + 1
        show_product_details(call.message, product_count=product_count, product_id=product_id, send_message=False)
    elif action == "minus" and int(product_count) > 0:
        product_count = int(product_count) - 1
        show_product_details(call.message, product_count=product_count, product_id=product_id, send_message=False)


@bot.callback_query_handler(func=lambda call: call.data.isdigit())
def answer_page_call(call):
    chat_id = call.message.chat.id
    message_id = call.message.id
    current_page = int(call.data)

    try:
        user_text = f"Список товаров в категории {DATA['category_name']}\n\n"
        start = (current_page - 1) * MAX_QUANTITY_PRODUCT_IN_PAGE
        last_index = current_page * MAX_QUANTITY_PRODUCT_IN_PAGE
        end = last_index if last_index <= DATA["count_product"] else DATA["count_product"]

        for i in range(start, end):
            product_id = DATA["products"][i][0]
            title = DATA["products"][i][1]
            price = DATA["products"][i][2]

            user_text += f"""{i + 1}. {title}
Стоимость: {price}
Подробнее: /product_{product_id}\n\n"""

        bot.edit_message_text(text=user_text, chat_id=chat_id,
                              message_id=message_id,
                              reply_markup=generate_pagination(DATA["total_pages"], current_page))
        bot.answer_callback_query(call.id, show_alert=False)
    except Exception:
        bot.answer_callback_query(call.id, "Текушая страница")


@bot.callback_query_handler(func=lambda call: "add" in call.data)
def add_product_in_cart(call):
    _, product_id, product_count, product_price = call.data.split("_")
    chat_id = call.message.chat.id

    # Получение карзины
    cursor.execute("""SELECT cart_id
    FROM carts
    WHERE user_id = (
        SELECT user_id
        FROM users
        WHERE telegram_id = %s
    )""", (chat_id,))
    cart_id = cursor.fetchone()

    # Добавление товара в корзину
    cursor.execute("""INSERT INTO cart_products (cart_id, product_id, quantity, price)
    VALUES ( %(cart_id)s, %(product_id)s, %(quantity)s, %(price)s )
    ON CONFLICT (cart_id, product_id) DO UPDATE
    SET price = cart_products.price + %(price)s,
    quantity = cart_products.quantity + %(quantity)s 
    WHERE cart_products.cart_id = %(cart_id)s AND cart_products.product_id = %(product_id)s AND cart_products.quantity +
    %(quantity)s < (
        SELECT in_storage
        FROM products
        WHERE product_id = %(product_id)s
    );


    UPDATE carts
    SET total_price = info.total_price,
    total_quantity = info.total_quantity
    FROM (
        SELECT SUM(quantity) as total_quantity, SUM(price) as total_price
        FROM cart_products
        WHERE cart_id = %(cart_id)s) as info
    WHERE cart_id = %(cart_id)s;
    """, {
        "cart_id": cart_id,
        "product_id": product_id,
        "quantity": product_count,
        "price": int(product_price) * int(product_price)
    })
    database.commit()
    bot.answer_callback_query(callback_query_id=call.id,
                              text="Добавлено")


@bot.message_handler(commands=["clear_cart"])
def cleaned_cart(message):
    chat_id = message.chat.id

    cursor.execute("""DELETE
    FROM cart_products
    WHERE cart_id = (
        SELECT cart_id
        FROM carts
        WHERE user_id = (
            SELECT user_id
            FROM users
            WHERE telegram_id = %s)
    );

    UPDATE carts
    SET total_price = 0,
    total_quantity = 0;
    """, (chat_id,))
    database.commit()
    bot.send_message(chat_id, "Корзина полностью очищена !")


@bot.callback_query_handler(func=lambda call: "pay" in call.data)
def pay_cart(call):
    _, cart_id = call.data.split("_")
    chat_id = call.message.chat.id

    # Получение общей стоимости корзины
    cursor.execute("""
        SELECT total_price
        FROM carts
        WHERE cart_id = %s
    """, (cart_id,))
    total_price = int(cursor.fetchone()[0])
    print(total_price)

    # Получение товаров из корзины
    cursor.execute("""SELECT title, cart_products.quantity, cart_products.price
    FROM cart_products
    JOIN products USING(product_id)
    WHERE cart_id = %s""", (cart_id,))
    products = cursor.fetchall()

    invoice_desc = "Вы выбрали: \n\n"
    i = 0
    for title, quantity, price in products:
        i += 1
        invoice_desc += f"""{i}. {title}
        Кол-во: {quantity}
        Стоимость: {price} сум\n\n"""
    # Создание чека
    INVOICE = {
        "chat_id": chat_id,
        "title": "Ваша корзина",
        "description": invoice_desc,
        "invoice_payload": "bot-defined invoice payload",
        "provider_token": os.getenv("PAYME_TOKEN"),
        "currency": "UZS",
        "prices": [LabeledPrice(label="Корзина", amount=int(str(total_price) + "00"))],
        "start_parameter": "pay",
        "is_flexible": False
    }
    try:
        bot.send_invoice(**INVOICE)
    except Exception:
        bot.send_message(chat_id, "Упс, что-то пошло не так :( ")


bot.polling(none_stop=True)
