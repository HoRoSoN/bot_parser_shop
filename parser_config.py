import psycopg2

database = psycopg2.connect(
    database="texnomart_wildberries",
    host="localhost",
    user="postgres",
    password="123456"
)
cursor = database.cursor()
