#!/usr/bin/env python3

import pandas as pd
import psycopg2
import clickhouse_connect
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Конфигурация PostgreSQL
PG_CONFIG = {
		'host': os.getenv('PG_HOST', 'localhost'),
		'port': os.getenv('PG_PORT', '5432'),
		'database': os.getenv('PG_DATABASE', 'raw_data'),
		'user': os.getenv('PG_USER', 'etl_user'),
		'password': os.getenv('PG_PASSWORD', '123')
}

# Конфигурация ClickHouse
CH_CONFIG = {
		'host': os.getenv('CH_HOST', 'localhost'),
		'port': int(os.getenv('CH_PORT', 8123)),
		'username': os.getenv('CH_USER', 'default'),
		'password': os.getenv('CH_PASSWORD', ''),
		'database': os.getenv('CH_DATABASE', 'analytics')
}

DATABASE_URL = f"postgresql://{PG_CONFIG['user']}:{PG_CONFIG['password']}@{PG_CONFIG['host']}:{PG_CONFIG['port']}/{PG_CONFIG['database']}"


def get_pg_connection():
#Создание соединения с PostgreSQL
		try:
				return psycopg2.connect(**PG_CONFIG)
		except psycopg2.Error as e:
				print(f"Ошибка подключения к PostgreSQL: {e}")
				sys.exit(1)


def get_ch_client():
#Создание соединения с ClickHouse
		try:
				return clickhouse_connect.get_client(**CH_CONFIG)
		except Exception as e:
				print(f"Ошибка подключения к ClickHouse: {e}")
				return None


def create_dds_schema():
#Создание схемы dds и таблиц
		ddl_sql = """
		CREATE SCHEMA IF NOT EXISTS dds;

		CREATE TABLE IF NOT EXISTS dds.dim_countries (
				country_code VARCHAR(2) PRIMARY KEY,
				country_name TEXT NOT NULL,
				loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		);

		CREATE TABLE IF NOT EXISTS dds.dim_users (
				user_id SERIAL PRIMARY KEY,
				user_email TEXT UNIQUE NOT NULL,
				user_name TEXT,
				user_country_code VARCHAR(2) REFERENCES dds.dim_countries(country_code),
				loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		);

		CREATE TABLE IF NOT EXISTS dds.dim_products (
				product_id SERIAL PRIMARY KEY,
				product_name TEXT UNIQUE NOT NULL,
				loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		);

		CREATE TABLE IF NOT EXISTS dds.fact_transactions (
				fact_id SERIAL PRIMARY KEY,
				user_id INTEGER NOT NULL REFERENCES dds.dim_users(user_id),
				product_id INTEGER NOT NULL REFERENCES dds.dim_products(product_id),
				quantity INTEGER NOT NULL CHECK (quantity > 0),
				price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
				total_amount DECIMAL(10,2) NOT NULL CHECK (total_amount >= 0),
				transaction_date TIMESTAMP NOT NULL,
				ip_address TEXT,
				source_system TEXT DEFAULT 'postgres',
				loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		);
		"""

		try:
				with get_pg_connection() as conn:
						with conn.cursor() as cur:
								cur.execute(ddl_sql)
						conn.commit()
				print("DDS схема и таблицы созданы/проверены")
		except Exception as e:
				print(f"Ошибка создания DDS схемы: {e}")
				sys.exit(1)


def create_dds_indexes():
#Создание индексов для DDS таблиц
		index_sql = """
		CREATE INDEX IF NOT EXISTS idx_fact_user_id ON dds.fact_transactions(user_id);
		CREATE INDEX IF NOT EXISTS idx_fact_product_id ON dds.fact_transactions(product_id);
		CREATE INDEX IF NOT EXISTS idx_fact_date ON dds.fact_transactions(transaction_date);
		CREATE INDEX IF NOT EXISTS idx_users_email ON dds.dim_users(user_email);
		CREATE INDEX IF NOT EXISTS idx_users_country ON dds.dim_users(user_country_code);
		CREATE INDEX IF NOT EXISTS idx_products_name ON dds.dim_products(product_name);
		"""

		try:
				with get_pg_connection() as conn:
						with conn.cursor() as cur:
								cur.execute(index_sql)
						conn.commit()
				print("Индексы для DDS созданы")
		except Exception as e:
				print(f"Ошибка создания индексов: {e}")


def load_dim_countries():
#Загрузка данных в dim_countries
		sql = """
		INSERT INTO dds.dim_countries (country_code, country_name)
		SELECT country_code, country_name FROM public.countries
		ON CONFLICT (country_code) 
		DO UPDATE SET country_name = EXCLUDED.country_name,
									loaded_at = CURRENT_TIMESTAMP;
		"""
		try:
				with get_pg_connection() as conn:
						with conn.cursor() as cur:
								cur.execute(sql)
						conn.commit()
				print("Загружены страны в dds.dim_countries")
		except Exception as e:
				print(f"Ошибка загрузки стран: {e}")


def load_dim_users():
#Загрузка данных в dim_users
		sql = """
		INSERT INTO dds.dim_users (user_email, user_name, user_country_code)
		SELECT DISTINCT user_email, user_name, user_country_code
		FROM public.raw_transactions
		WHERE user_email IS NOT NULL
		ON CONFLICT (user_email) 
		DO UPDATE SET user_name = EXCLUDED.user_name,
									user_country_code = EXCLUDED.user_country_code,
									loaded_at = CURRENT_TIMESTAMP;
		"""
		try:
				with get_pg_connection() as conn:
						with conn.cursor() as cur:
								cur.execute(sql)
						conn.commit()
				print("Загружены пользователи в dds.dim_users")
		except Exception as e:
				print(f"Ошибка загрузки пользователей: {e}")


def load_dim_products():
#Загрузка данных в dim_products
		sql = """
		INSERT INTO dds.dim_products (product_name)
		SELECT DISTINCT product_name
		FROM public.raw_transactions
		WHERE product_name IS NOT NULL
		ON CONFLICT (product_name) 
		DO UPDATE SET loaded_at = CURRENT_TIMESTAMP;
		"""
		try:
				with get_pg_connection() as conn:
						with conn.cursor() as cur:
								cur.execute(sql)
						conn.commit()
				print("Загружены товары в dds.dim_products")
		except Exception as e:
				print(f"Ошибка загрузки товаров: {e}")


def load_fact_transactions():
#Загрузка данных в fact_transactions
		sql = """
		INSERT INTO dds.fact_transactions 
				(user_id, product_id, quantity, price, total_amount, 
				 transaction_date, ip_address, source_system)
		SELECT 
				du.user_id,
				dp.product_id,
				rt.quantity,
				rt.price,
				rt.total_amount,
				rt.transaction_date,
				rt.ip_address,
				rt.source_system
		FROM public.raw_transactions rt
		JOIN dds.dim_users du ON du.user_email = rt.user_email
		JOIN dds.dim_products dp ON dp.product_name = rt.product_name
		ON CONFLICT (fact_id) DO NOTHING;
		"""
		try:
				with get_pg_connection() as conn:
						with conn.cursor() as cur:
								cur.execute(sql)
						conn.commit()
				print("Загружены транзакции в dds.fact_transactions")
		except Exception as e:
				print(f"Ошибка загрузки транзакций: {e}")


def create_clickhouse_table():
#Создание таблицы в ClickHouse
		ch_client = get_ch_client()
		if not ch_client:
				return False

		create_sql = """
		CREATE TABLE IF NOT EXISTS transactions_stats_by_countries (
				country_code String,
				country_name String,
				total_sales Decimal(15,2),
				avg_transaction_value Decimal(15,2),
				transaction_count UInt64,
				updated_at DateTime DEFAULT now()
		) ENGINE = ReplacingMergeTree(updated_at)
		ORDER BY country_code
		"""
		try:
				ch_client.command(create_sql)
				print("Таблица ClickHouse создана")
				return True
		except Exception as e:
				print(f"Ошибка создания таблицы ClickHouse: {e}")
				return False


def update_clickhouse_stats():
#Обновление статистики в ClickHouse
		ch_client = get_ch_client()
		if not ch_client:
				return

		engine = create_engine(DATABASE_URL)

		query = """
		SELECT 
				c.country_code,
				c.country_name,
				COALESCE(SUM(ft.total_amount), 0) AS total_sales,
				COALESCE(AVG(ft.total_amount), 0) AS avg_transaction_value,
				COUNT(ft.fact_id) AS transaction_count
		FROM dds.dim_countries c
		LEFT JOIN dds.dim_users du ON c.country_code = du.user_country_code
		LEFT JOIN dds.fact_transactions ft ON du.user_id = ft.user_id
		GROUP BY c.country_code, c.country_name
		ORDER BY total_sales DESC
		"""

		try:
				df = pd.read_sql(query, engine)
				if df.empty:
						print("Нет данных для загрузки в ClickHouse")
						return

				ch_client.command("TRUNCATE TABLE transactions_stats_by_countries")
				ch_client.insert_df('transactions_stats_by_countries', df)

				print(f"Статистика обновлена: {len(df)} стран")
		except Exception as e:
				print(f"Ошибка обновления ClickHouse: {e}")

def run_transform_and_load():
#Запуск трансформации и загрузки
		print("=" * 60)
		print("Запуск Transform & Load (raw → DDS → ClickHouse)")
		print("=" * 60)

		create_dds_schema()
		load_dim_countries()
		load_dim_users()
		load_dim_products()
		load_fact_transactions()
		create_dds_indexes()

		if create_clickhouse_table():
				update_clickhouse_stats()

		print("=" * 60)
		print("Transform & Load завершен!")
		print("=" * 60)

if __name__ == "__main__":
		run_transform_and_load()