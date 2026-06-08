"""
ETL Pipeline DAG
Задача: Транзакции из PostgreSQL → DDS слой → Статистика в ClickHouse
Запуск: ежедневно в 2:00
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow_clickhouse_plugin.hooks.clickhouse import ClickHouseHook
from airflow.models import Variable
import pandas as pd
import requests
import logging

# Настройка логгера
logger = logging.getLogger(__name__)

# Аргументы по умолчанию
default_args = {
		'owner': 'data_engineer',
		'depends_on_past': False,
		'start_date': datetime(2024, 1, 1),
		'email_on_failure': False,
		'email_on_retry': False,
		'retries': 2,
		'retry_delay': timedelta(minutes=5),
}

# Определение DAG
dag = DAG(
		'etl_transactions_pipeline',
		default_args=default_args,
		description='ETL: PostgreSQL raw → DDS → ClickHouse',
		schedule_interval='0 2 * * *',  # Ежедневно в 2:00
		catchup=False,
		tags=['etl', 'transactions', 'dds'],
)


def fetch_and_load_countries(**context):
#Загрузка данных о странах из API в PostgreSQL
		url = Variable.get('COUNTRIES_API_URL', 'https://restcountries.com/v3.1/all?fields=name,cca2')

		try:
				response = requests.get(url, verify=False, timeout=30)
				response.raise_for_status()
				countries = response.json()

				country_list = []
				for country in countries:
						cca2 = country.get('cca2')
						name = country.get("name", {}).get("common")
						if cca2 and name and len(cca2) == 2:
								country_list.append((cca2, name))

				pg_hook = PostgresHook(postgres_conn_id='postgres_default')

				upsert_sql = """
				INSERT INTO public.countries (country_code, country_name)
				VALUES (%s, %s)
				ON CONFLICT (country_code) 
				DO UPDATE SET country_name = EXCLUDED.country_name,
											loaded_at = CURRENT_TIMESTAMP;
				"""

				with pg_hook.get_conn() as conn:
						with conn.cursor() as cur:
								for code, name in country_list:
										cur.execute(upsert_sql, (code, name))
						conn.commit()

				logger.info(f"Загружено {len(country_list)} стран")
				context['ti'].xcom_push(key='countries_count', value=len(country_list))

		except Exception as e:
				logger.error(f"Ошибка загрузки стран: {e}")
				raise


def check_raw_transactions(**context):
#Проверка наличия данных в raw_transactions
		pg_hook = PostgresHook(postgres_conn_id='postgres_default')
		
		sql = "SELECT COUNT(*) FROM public.raw_transactions"
		result = pg_hook.get_first(sql)
		
		count = result[0] if result else 0
		logger.info(f"В raw_transactions найдено {count} записей")

		if count == 0:
				raise ValueError("Нет данных в raw_transactions!")

		context['ti'].xcom_push(key='raw_count', value=count)
		return count


def create_dds_tables(**context):
#Создание DDS таблиц в PostgreSQL
		pg_hook = PostgresHook(postgres_conn_id='postgres_default')

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
				pg_hook.run(ddl_sql)
				logger.info("DDS таблицы созданы/проверены")
		except Exception as e:
				logger.error(f"Ошибка создания DDS таблиц: {e}")
				raise


def load_dim_countries(**context):
#Загрузка данных в dim_countries
		pg_hook = PostgresHook(postgres_conn_id='postgres_default')

		sql = """
		INSERT INTO dds.dim_countries (country_code, country_name)
		SELECT country_code, country_name FROM public.countries
		ON CONFLICT (country_code) 
		DO UPDATE SET country_name = EXCLUDED.country_name,
									loaded_at = CURRENT_TIMESTAMP;
		"""

		try:
				pg_hook.run(sql)
				logger.info("Загружены страны в dds.dim_countries")
		except Exception as e:
				logger.error(f"Ошибка загрузки стран: {e}")
				raise


def load_dim_users(**context):
#Загрузка данных в dim_users
		pg_hook = PostgresHook(postgres_conn_id='postgres_default')

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
				pg_hook.run(sql)
				logger.info("Загружены пользователи в dds.dim_users")
		except Exception as e:
				logger.error(f"Ошибка загрузки пользователей: {e}")
				raise


def load_dim_products(**context):
#Загрузка данных в dim_products
		pg_hook = PostgresHook(postgres_conn_id='postgres_default')
		
		sql = """
		INSERT INTO dds.dim_products (product_name)
		SELECT DISTINCT product_name
		FROM public.raw_transactions
		WHERE product_name IS NOT NULL
		ON CONFLICT (product_name) 
		DO UPDATE SET loaded_at = CURRENT_TIMESTAMP;
		"""

		try:
				pg_hook.run(sql)
				logger.info("Загружены товары в dds.dim_products")
		except Exception as e:
				logger.error(f"Ошибка загрузки товаров: {e}")
				raise


def load_fact_transactions(**context):
#Загрузка данных в fact_transactions
		pg_hook = PostgresHook(postgres_conn_id='postgres_default')

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
				pg_hook.run(sql)
				logger.info("Загружены транзакции в dds.fact_transactions")
		except Exception as e:
				logger.error(f"Ошибка загрузки транзакций: {e}")
				raise


def create_dds_indexes(**context):
#Создание индексов для DDS таблиц
		pg_hook = PostgresHook(postgres_conn_id='postgres_default')

		index_sql = """
		CREATE INDEX IF NOT EXISTS idx_fact_user_id ON dds.fact_transactions(user_id);
		CREATE INDEX IF NOT EXISTS idx_fact_product_id ON dds.fact_transactions(product_id);
		CREATE INDEX IF NOT EXISTS idx_fact_date ON dds.fact_transactions(transaction_date);
		CREATE INDEX IF NOT EXISTS idx_users_email ON dds.dim_users(user_email);
		CREATE INDEX IF NOT EXISTS idx_users_country ON dds.dim_users(user_country_code);
		CREATE INDEX IF NOT EXISTS idx_products_name ON dds.dim_products(product_name);
		"""

		try:
				pg_hook.run(index_sql)
				logger.info("Индексы для DDS созданы")
		except Exception as e:
				logger.warning(f"Ошибка создания индексов: {e}")


def create_clickhouse_table(**context):
#Создание таблицы в ClickHouse
		ch_hook = ClickHouseHook(clickhouse_conn_id='clickhouse_default')

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
				ch_hook.run(create_sql)
				logger.info("Таблица ClickHouse создана/проверена")
		except Exception as e:
				logger.error(f"Ошибка создания таблицы ClickHouse: {e}")
				raise


def update_clickhouse_stats(**context):
#Обновление статистики в ClickHouse
		pg_hook = PostgresHook(postgres_conn_id='postgres_default')
		ch_hook = ClickHouseHook(clickhouse_conn_id='clickhouse_default')
		
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
# Получаем данные из PostgreSQL
				engine = pg_hook.get_sqlalchemy_engine()
				df = pd.read_sql(query, engine)

				if df.empty:
						logger.warning("Нет данных для загрузки в ClickHouse")
						return

# Очищаем таблицу в ClickHouse
				ch_hook.run("TRUNCATE TABLE transactions_stats_by_countries")

# Вставляем данные в ClickHouse
				ch_hook.insert_rows(
						table='transactions_stats_by_countries',
						rows=df.values.tolist(),
						target_fields=df.columns.tolist()
				)

				logger.info(f"Статистика обновлена: {len(df)} стран")
				context['ti'].xcom_push(key='stats_count', value=len(df))
				
		except Exception as e:
				logger.error(f"Ошибка обновления ClickHouse: {e}")
				raise


def send_notification(**context):
#Отправка уведомления о завершении
		raw_count = context['ti'].xcom_pull(task_ids='check_raw_transactions', key='raw_count')
		stats_count = context['ti'].xcom_pull(task_ids='update_clickhouse_stats', key='stats_count')
		
		logger.info("=" * 60)
		logger.info(f"ИТОГИ ETL ПАЙПЛАЙНА:")
		logger.info(f"   - Обработано транзакций: {raw_count}")
		logger.info(f"   - Стран в статистике: {stats_count}")
		logger.info(f"   - Статус: УСПЕШНО")
		logger.info("=" * 60)


# Определение задач DAG
start = EmptyOperator(task_id='start', dag=dag)

fetch_countries = PythonOperator(
		task_id='fetch_and_load_countries',
		python_callable=fetch_and_load_countries,
		dag=dag,
)

check_raw = PythonOperator(
		task_id='check_raw_transactions',
		python_callable=check_raw_transactions,
		dag=dag,
)

create_tables = PythonOperator(
		task_id='create_dds_tables',
		python_callable=create_dds_tables,
		dag=dag,
)

load_countries = PythonOperator(
		task_id='load_dim_countries',
		python_callable=load_dim_countries,
		dag=dag,
)

load_users = PythonOperator(
		task_id='load_dim_users',
		python_callable=load_dim_users,
		dag=dag,
)

load_products = PythonOperator(
		task_id='load_dim_products',
		python_callable=load_dim_products,
		dag=dag,
)

load_facts = PythonOperator(
		task_id='load_fact_transactions',
		python_callable=load_fact_transactions,
		dag=dag,
)

create_indexes = PythonOperator(
		task_id='create_dds_indexes',
		python_callable=create_dds_indexes,
		dag=dag,
)

create_ch_table = PythonOperator(
		task_id='create_clickhouse_table',
		python_callable=create_clickhouse_table,
		dag=dag,
)

update_stats = PythonOperator(
		task_id='update_clickhouse_stats',
		python_callable=update_clickhouse_stats,
		dag=dag,
)

notify = PythonOperator(
		task_id='send_notification',
		python_callable=send_notification,
		dag=dag,
)

end = EmptyOperator(task_id='end', dag=dag)

# Сборка зависимостей
start >> [fetch_countries, check_raw] >> create_tables
create_tables >> [load_countries, load_users, load_products] >> load_facts
load_facts >> create_indexes >> create_ch_table >> update_stats >> notify >> end