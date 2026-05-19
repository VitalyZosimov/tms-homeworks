import sqlite3
import pandas as pd
import psycopg2
import requests
from sqlalchemy import create_engine, text
import clickhouse_connect
import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

PG_HOST = os.getenv('PG_HOST', 'localhost')
PG_PORT = os.getenv('PG_PORT', '5432')
PG_DATABASE = os.getenv('PG_DATABASE', 'raw_data')
PG_USER = os.getenv('PG_USER', 'etl_user')
PG_PASSWORD = os.getenv('PG_PASSWORD', '123')

CH_HOST = os.getenv('CH_HOST', 'localhost')
CH_PORT = int(os.getenv('CH_PORT', 8123))
CH_USER = os.getenv('CH_USER', 'etl_user')
CH_PASSWORD = os.getenv('CH_PASSWORD', '123')
CH_DATABASE = os.getenv('CH_DATABASE', 'analytics')

COUNTRIES_API_URL = os.getenv('COUNTRIES_API_URL', 'https://restcountries.com/v3.1/all?fields=name,cca2')

DATABASE_URL = f'postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}'


def get_pg_connection():
    """Возвращает соединение с PostgreSQL"""
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        database=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD
    )


def create_tables():
    """
    Создание таблиц для staging слоя
    """
    with get_pg_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                    create table if not exists countries (
                country_code VARCHAR(2) primary key,
                country_name TEXT not null,
                loaded_at  timestamp default CURRENT_TIMESTAMP
                )
            """)
            
            cur.execute("""
                    CREATE TABLE IF NOT EXISTS raw_transactions (
                id SERIAL PRIMARY KEY,
                user_name TEXT,
                user_email TEXT,
                user_country_code VARCHAR(2),  -- код страны
                product_name TEXT,
                quantity INTEGER,
                price DECIMAL(10, 2),
                total_amount DECIMAL(10, 2),
                transaction_date TIMESTAMP,
                ip_address TEXT,
                source_system TEXT DEFAULT 'sqlite',
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        conn.commit()


def get_from_staging():
    """
    Забираем сырые данные из source_data.db
    """
    connection = sqlite3.connect("34_hw/source_data.db")
    cursor = connection.cursor()
    cursor.execute('''SELECT * FROM transactions''')
    data = cursor.fetchall()
    connection.close()
    return data


def get_countries():
    """
    Забираем данные по странам
    """
    url = COUNTRIES_API_URL
    response = requests.get(url, verify=False)
    countries = response.json()
    country_list = []
    for country in countries:
        cca2 = country.get('cca2')
        name = country.get("name", {}).get("common")
        if cca2 and name:
            country_list.append((cca2, name))
    return country_list


def load_countries(data):
    """
    Загрузка данных по странам в raw schema
    """
    with get_pg_connection() as conn:
        with conn.cursor() as cur:
            for code, name in data:
                cur.execute("""INSERT INTO public.countries (country_code, country_name) VALUES (%s, %s) ON CONFLICT (country_code) DO NOTHING""", (code, name))
        conn.commit()
        

def load_transactions(data):
    """
    Загрузка сырых данных по транзакциям
    """
    with get_pg_connection() as conn:
        with conn.cursor() as cur:
            for row in data:
                cur.execute("""INSERT INTO public.raw_transactions (id, user_name, user_email, user_country_code, product_name, quantity, price, total_amount, transaction_date, ip_address) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING""", row)
        conn.commit()
        

def create_dds_indexes():
    """Создание индексов для DDS таблиц"""
    try:
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                print("Creating indexes...")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_fact_user_id ON dds.fact_sales(user_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_fact_product_id ON dds.fact_sales(product_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_fact_date ON dds.fact_sales(transaction_date)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON dds.dim_users(user_email)")
                print("Indexes created!!")
            conn.commit()
    except Exception as e:
        print(e)


def dds_create():
    """
    Создание полноценного DDS слоя на основе сырых данных
    """
    engine = create_engine(DATABASE_URL)
    
    df_raw = pd.read_sql("SELECT * FROM public.raw_transactions", engine)
    
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS dds"))
        conn.commit()
        
    # Данные по странам
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dds.dim_countries (
                country_code VARCHAR(2) PRIMARY KEY,
                country_name TEXT
            )
        """))
        
        conn.execute(text("""
            INSERT INTO dds.dim_countries (country_code, country_name)
            SELECT country_code, country_name FROM public.countries
            ON CONFLICT (country_code) DO NOTHING
        """))
        conn.commit()
    

    # Данные по клиентам
    df_users = df_raw[['user_email', 'user_name', 'user_country_code']].drop_duplicates()
    
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dds.dim_users (
                user_id SERIAL PRIMARY KEY,
                user_email TEXT UNIQUE,
                user_name TEXT,
                user_country_code VARCHAR(2) REFERENCES dds.dim_countries(country_code)
            )
        """))
        
        for _, row in df_users.iterrows():
            conn.execute(
                text("""
                    INSERT INTO dds.dim_users (user_email, user_name, user_country_code)
                    VALUES (:email, :name, :country_code)
                    ON CONFLICT (user_email) DO NOTHING
                """),
                {"email": row['user_email'], "name": row['user_name'], "country_code": row['user_country_code']}
            )
        conn.commit()
    
    # Данные по товарам
    df_products = df_raw[['product_name']].drop_duplicates()
    
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dds.dim_products (
                product_id SERIAL PRIMARY KEY,
                product_name TEXT UNIQUE
            )
        """))
        
        for _, row in df_products.iterrows():
            conn.execute(
                text("""
                    INSERT INTO dds.dim_products (product_name)
                    VALUES (:product_name)
                    ON CONFLICT (product_name) DO NOTHING
                """),
                {"product_name": row['product_name']}
            )
        conn.commit()
    
    # Данные по транзакциям (мерджим таблицы клиентов и продуктов по ключевым полям, т.к. id в оригинале отсутствует)
    df_users_db = pd.read_sql("SELECT user_id, user_email FROM dds.dim_users", engine)
    df_products_db = pd.read_sql("SELECT product_id, product_name FROM dds.dim_products", engine)
    
    df_fact = df_raw.merge(df_users_db, on='user_email', how='inner')
    df_fact = df_fact.merge(df_products_db, on='product_name', how='inner')
    
    df_fact = df_fact[['user_id', 'product_id', 'quantity', 'price', 'total_amount', 
                        'transaction_date', 'ip_address', 'source_system']]
    
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dds.fact_sales (
                fact_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES dds.dim_users(user_id),
                product_id INTEGER REFERENCES dds.dim_products(product_id),
                quantity INTEGER,
                price DECIMAL(10,2),
                total_amount DECIMAL(10,2),
                transaction_date TIMESTAMP,
                ip_address TEXT,
                source_system TEXT,
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        for _, row in df_fact.iterrows():
            conn.execute(
                text("""
                    INSERT INTO dds.fact_sales (user_id, product_id, quantity, price, total_amount, transaction_date, ip_address, source_system)
                    VALUES (:user_id, :product_id, :quantity, :price, :total_amount, :transaction_date, :ip_address, :source_system)
                """),
                {
                    "user_id": int(row['user_id']),
                    "product_id": int(row['product_id']),
                    "quantity": row['quantity'],
                    "price": float(row['price']),
                    "total_amount": float(row['total_amount']),
                    "transaction_date": row['transaction_date'],
                    "ip_address": row['ip_address'],
                    "source_system": row['source_system']
                }
            )
        # create_dds_indexes()
        print("DDS Created!")
        conn.commit()
    

def update_clickhouse_stats():
    """
    Обновление статистики в ClickHouse (truncate + insert)
    """
    try:
        ch_client = clickhouse_connect.get_client(
            host=CH_HOST,
            port=CH_PORT,
            username=CH_USER,
            password=CH_PASSWORD,
            database=CH_DATABASE
        )

        ch_client.command("""
            CREATE TABLE IF NOT EXISTS transactions_stats_by_countries (
                country_code String,
                country_name String,
                total_sales Decimal(15,2),
                avg_transaction_value Decimal(15,2),
                transaction_count UInt64,
                updated_at DateTime DEFAULT now()
            ) ENGINE = ReplacingMergeTree(updated_at)
            ORDER BY country_code
        """)

        ch_client.command("TRUNCATE TABLE transactions_stats_by_countries")

        engine = create_engine(DATABASE_URL)
        
        query = """
            SELECT 
                c.country_code,
                c.country_name,
                COALESCE(SUM(fs.total_amount), 0) AS total_sales,
                COALESCE(AVG(fs.total_amount), 0) AS avg_transaction_value,
                COUNT(fs.fact_id) AS transaction_count
            FROM dds.dim_countries c
            LEFT JOIN dds.dim_users du ON c.country_code = du.user_country_code
            LEFT JOIN dds.fact_sales fs ON du.user_id = fs.user_id
            GROUP BY c.country_code, c.country_name
            ORDER BY total_sales DESC
        """
        
        df = pd.read_sql(query, engine)
        
        if df.empty:
            print("⚠️ Нет данных для загрузки в ClickHouse")
            return

        ch_client.insert_df('transactions_stats_by_countries', df)
        
    except Exception as e:
        print(f"{e}")


if __name__ == "__main__":
    create_tables()
    countries = get_countries()
    raw_data = get_from_staging()
    load_countries(countries)
    load_transactions(raw_data)
    dds_create()
    update_clickhouse_stats()