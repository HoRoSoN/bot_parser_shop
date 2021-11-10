import requests
from bs4 import BeautifulSoup
from parser_config import database, cursor
from bot_config import CATEGORIES


class Parser:
    def __init__(self, page_name, category_id, max_product=10):
        self.URL = f'https://texnomart.uz/ru/katalog/{page_name}'
        self.HOST = 'https://texnomart.uz'
        self.max_product = max_product
        self.category_id = category_id
        self.HEADERS = {
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                          ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_html(self, url):
        response = requests.get(url, headers=self.HEADERS)
        try:
            response.raise_for_status()
            return response.text
        except requests.HTTPError:
            print('Ошибка')

    def get_data(self, html):
        soup = BeautifulSoup(html, 'lxml')
        product_links = [self.HOST + link.find('a', class_='name').get('href') for link in
                         soup.find_all('div', class_="proporties")]

        for links in product_links[:self.max_product]:
            single_page = self.get_html(links)
            soup = BeautifulSoup(single_page, 'lxml')

            product_name = soup.find('h1', class_='title').get_text(strip=True)
            product_price = soup.find('span', class_='price').get_text(strip=True)
            product_photo = self.HOST + soup.find("a", class_="swiper-slide")["href"]

            characteristics = ''
            characteristic_products = soup.find('tbody', class_='row').find_all('tr', class_='col-sm-6')
            brand = ''
            i = 0
            for characteristic in characteristic_products:
                if i == 0:
                    key, value = characteristic.find_all('td')
                    brand += f"{key.get_text(strip=True)} {value.get_text(strip=True)}"
                    i += 1
                else:
                    key, value = characteristic.find_all('td')
                    characteristics += f"{key.get_text(strip=True)} {value.get_text(strip=True)}\n"
            i = 0

            cursor.execute("""INSERT INTO products (title, brand, price, image, link, characteristics, category_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT(title, link) DO NOTHING
            """, (product_name, brand, product_price, product_photo, links, characteristics, self.category_id))
            database.commit()
        return True

    def get_run(self):
        html = self.get_html(self.URL)
        status = self.get_data(html)
        if status:
            print('Данные успешно сохранены!!')


def start_parser():
    for category_name, category_value in CATEGORIES.items():
        print(f'Сейчас парсим категорию - {category_name}')
        parser = Parser(category_value['page_name'], category_value['category_id'])
        parser.get_run()


def insert_categories():
    for category_name in CATEGORIES.keys():
        cursor.execute('''
        INSERT INTO CATEGORIES (category_title) VALUES (%s)
        ON CONFLICT (category_title) DO NOTHING
        ''', (category_name,))
        database.commit()


insert_categories()
start_parser()
database.close()
