#!/usr/bin/env python3

import psycopg2
import requests
import os
import sys
from dotenv import load_dotenv
from typing import List, Tuple

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

# Конфигурация API
COUNTRIES_API_URL = os.getenv('COUNTRIES_API_URL', 'https://restcountries.com/v3.1/all?fields=name,cca2')

def get_pg_connection():
		"""Создание соединения с PostgreSQL"""
		try:
				conn = psycopg2.connect(**PG_CONFIG)
				return conn
		except psycopg2.Error as e:
				print(f"Ошибка подключения к PostgreSQL: {e}")
				sys.exit(1)

def create_staging_tables():
		"""Создание таблиц staging слоя в PostgreSQL (если не существуют)"""
		create_table_sql = """
		CREATE TABLE IF NOT EXISTS public.countries (
				country_code VARCHAR(2) PRIMARY KEY,
				country_name TEXT NOT NULL,
				loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		);

		CREATE TABLE IF NOT EXISTS public.raw_transactions (
				id SERIAL PRIMARY KEY,
				user_name TEXT,
				user_email TEXT,
				user_country_code VARCHAR(2),
				product_name TEXT,
				quantity INTEGER,
				price DECIMAL(10, 2),
				total_amount DECIMAL(10, 2),
				transaction_date TIMESTAMP,
				ip_address TEXT,
				source_system TEXT DEFAULT 'postgres',
				loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		);
		"""

		try:
				with get_pg_connection() as conn:
						with conn.cursor() as cur:
								cur.execute(create_table_sql)
						conn.commit()
				print("Staging таблицы созданы/проверены")
		except Exception as e:
				print(f"Ошибка создания таблиц: {e}")
				sys.exit(1)


def fetch_countries() -> List[Tuple[str, str]]:
#Загрузка данных о странах из API
		try:
				response = requests.get(COUNTRIES_API_URL, verify=False, timeout=30)
				response.raise_for_status()
				countries = response.json()

				country_list = []
				for country in countries:
						cca2 = country.get('cca2')
						name = country.get("name", {}).get("common")
						if cca2 and name and len(cca2) == 2:
								country_list.append((cca2, name))

				print(f"Загружено {len(country_list)} стран из API")
				return country_list
		except requests.RequestException as e:
				print(f"Ошибка загрузки стран: {e}")
				return []

def upsert_countries(countries: List[Tuple[str, str]]):
#UPSERT стран в PostgreSQL
		upsert_sql = """
		INSERT INTO public.countries (country_code, country_name)
		VALUES (%s, %s)
		ON CONFLICT (country_code) 
		DO UPDATE SET country_name = EXCLUDED.country_name,
									loaded_at = CURRENT_TIMESTAMP;
		"""

		try:
				with get_pg_connection() as conn:
						with conn.cursor() as cur:
								for code, name in countries:
										cur.execute(upsert_sql, (code, name))
						conn.commit()
				print(f"Загружено {len(countries)} стран в PostgreSQL (UPSERT)")
		except Exception as e:
				print(f"Ошибка загрузки стран: {e}")


def check_raw_transactions():
#Проверка наличия данных в raw_transactions
		try:
				with get_pg_connection() as conn:
						with conn.cursor() as cur:
								cur.execute("SELECT COUNT(*) FROM public.raw_transactions")
								count = cur.fetchone()[0]
								print(f"В raw_transactions найдено {count} записей")
								return count > 0
		except Exception as e:
				print(f"Таблица raw_transactions пуста или не существует: {e}")
				return False


def run_extract_and_load():
#Запуск процесса подготовки данных
		print("=" * 60)
		print("Запуск ETL: Подготовка данных в PostgreSQL")
		print("=" * 60)

# 1. Создание таблиц
		create_staging_tables()

# 2. Загрузка стран
		countries = fetch_countries()
		if countries:
				upsert_countries(countries)

# 3. Проверка данных
		has_data = check_raw_transactions()

		if not has_data:
				print("ВНИМАНИЕ: Таблица raw_transactions пуста!")
				print("Сначала загрузите данные в raw_transactions")

		print("=" * 60)
		print("Extract & Load завершен успешно!")
		print("=" * 60)

if __name__ == "__main__":
		run_extract_and_load()