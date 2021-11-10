def get_total_pages(count_products, max_quantity=3):
    pages = count_products // max_quantity
    if count_products % max_quantity != 0:
        pages += 1
        return pages


def cleaned_price(price):
    """ Возвращает очищеную стоимость товара,
     Только цифры"""
    clear_price = price.replace("cумc учетом НДС", "").replace(" ", "")
    return clear_price
