from parser_config import database, cursor


def create_categories():
    cursor.execute('drop table if exists categories CASCADE')
    cursor.execute('''CREATE TABLE IF NOT EXISTS categories(
        category_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        category_title VARCHAR(30) NOT NULL UNIQUE
    )
''')


def create_products():
    cursor.execute('drop table products CASCADE')
    cursor.execute("""CREATE TABLE IF NOT EXISTS products(
        product_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        title VARCHAR(255),
        brand VARCHAR(255),
        price TEXT,
        image TEXT,
        link TEXT,
        characteristics TEXT,
        in_storage INTEGER,
        category_id INTEGER NOT NULL,
        
        UNIQUE(title, link),
        FOREIGN KEY(category_id) REFERENCES categories(category_id)
    );
""")


def create_users():
    cursor.execute('drop table if exists users CASCADE')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        telegram_id INTEGER NOT NULL UNIQUE,
        first_name VARCHAR(30),
        last_name VARCHAR(30),
        phone VARCHAR(30)
    )
''')


def create_cart():
    cursor.execute('drop table if exists carts CASCADE')
    cursor.execute("""CREATE TABLE IF NOT EXISTS carts(
        cart_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        user_id INTEGER NOT NULL UNIQUE,
        total_quantity INTEGER DEFAULT 0,
        total_price INTEGER DEFAULT 0,
    
        FOREIGN KEY(user_id) REFERENCES users(user_id)
)""")


def create_cart_products():
    cursor.execute('drop table cart_products CASCADE')
    cursor.execute("""CREATE TABLE IF NOT EXISTS cart_products(
        cart_product_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        cart_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER DEFAULT 1,
        price INTEGER,
    
        FOREIGN KEY(cart_id) REFERENCES carts(cart_id),
        FOREIGN KEY(product_id) REFERENCES products(product_id),
        UNIQUE (cart_id, product_id)
)""")


create_users()
create_cart()
create_cart_products()

database.commit()
database.close()
