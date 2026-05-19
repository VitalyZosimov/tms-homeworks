#ФУнкции для работы с БД
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow_clickhouse_plugin.hooks.clickhouse import ClickHouseHook
import logging

logger = logging.getLogger(__name__)


def get_postgres_connection():
#Получение соединения с PostgreSQL
		try:
				hook = PostgresHook(postgres_conn_id='postgres_default')
				return hook.get_conn()
		except Exception as e:
				logger.error(f"Ошибка подключения к PostgreSQL: {e}")
				raise


def get_clickhouse_client():
#Получение клиента ClickHouse
		try:
				hook = ClickHouseHook(clickhouse_conn_id='clickhouse_default')
				return hook.get_conn()
		except Exception as e:
				logger.error(f"Ошибка подключения к ClickHouse: {e}")
				raise


def execute_postgres(sql: str, autocommit: bool = True):
#Выполнение SQL в PostgreSQL
		hook = PostgresHook(postgres_conn_id='postgres_default')
		return hook.run(sql, autocommit=autocommit)


def execute_clickhouse(sql: str):
#Выполнение SQL в ClickHouse
		hook = ClickHouseHook(clickhouse_conn_id='clickhouse_default')
		return hook.run(sql)