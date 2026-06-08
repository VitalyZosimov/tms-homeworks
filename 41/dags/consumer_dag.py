# consumer_dag.py
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from clickhouse_driver import Client
import logging

logger = logging.getLogger(__name__)

CREATE_CLICKHOUSE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS dm_hw41_support_report (
		report_ts DateTime,
		window_start String,
		window_end String,
		tickets_count UInt64,
		users_count UInt64,
		avg_resolution_minutes Float64,
		urgent_tickets_count UInt64
)
ENGINE = MergeTree
ORDER BY report_ts
"""

AGGREGATION_SQL = """
SELECT 
		COUNT(*) as tickets_count,
		COUNT(DISTINCT user_id) as users_count,
		AVG(resolution_minutes) as avg_resolution_minutes,
		SUM(CASE WHEN priority = 'urgent' THEN 1 ELSE 0 END) as urgent_tickets_count
FROM stg_hw41_support_valid_tickets
WHERE loaded_at >= %s AND loaded_at < %s
"""

def aggregate_and_load_to_clickhouse(**context):
#Агрегация данных из PostgreSQL и загрузка отчета в ClickHouse

		data_interval_start = context['data_interval_start']
		window_end = data_interval_start
		window_start = window_end - timedelta(hours=1)

		logger.info(f"Агрегация данных за окно: {window_start} - {window_end}")

# 1. Подключаемся к PostgreSQL
		pg_hook = PostgresHook(postgres_conn_id='postgres_default')
		result = pg_hook.get_first(AGGREGATION_SQL, parameters=(window_start, window_end))

		if not result or result[0] == 0:
				logger.warning(f"Нет данных за период {window_start} - {window_end}")
				return

		tickets_count, users_count, avg_resolution, urgent_tickets = result

		logger.info(f"Метрики: тикетов={tickets_count}, пользователей={users_count}")

# 2. Подключаемся к ClickHouse напрямую
		ch_client = Client(
				host='localhost',     #  хост
				port=9000,            #  порт для нативного протокола
				user='default',       
				password='',          
				database='default'
		)

# Создаём таблицу
		ch_client.execute(CREATE_CLICKHOUSE_TABLE_SQL)

# Вставляем данные
		insert_sql = """
		INSERT INTO dm_hw41_support_report 
		(report_ts, window_start, window_end, tickets_count, users_count, 
		avg_resolution_minutes, urgent_tickets_count)
		VALUES (%(report_ts)s, %(window_start)s, %(window_end)s, %(tickets_count)s,
						%(users_count)s, %(avg_resolution_minutes)s, %(urgent_tickets)s)
		"""

		ch_client.execute(insert_sql, {
				'report_ts': datetime.now(),
				'window_start': window_start.isoformat(),
				'window_end': window_end.isoformat(),
				'tickets_count': tickets_count,
				'users_count': users_count,
				'avg_resolution_minutes': float(avg_resolution) if avg_resolution else 0.0,
				'urgent_tickets': urgent_tickets
		})

		ch_client.disconnect()
		logger.info(f"Отчет загружен в ClickHouse")

# DAG определение остаётся без изменений
default_args = {
		'owner': 'airflow',
		'depends_on_past': False,
		'start_date': datetime(2026, 1, 1),
		'retries': 1,
		'retry_delay': timedelta(minutes=5),
}

with DAG(
		'support_tickets_consumer',
		default_args=default_args,
		description='Consumer DAG: Postgres -> ClickHouse',
		schedule=None,  # или ['@daily']
		catchup=False,
		tags=['etl', 'consumer'],
) as dag:

		aggregate_load = PythonOperator(
				task_id='aggregate_and_load_to_clickhouse',
			python_callable=aggregate_and_load_to_clickhouse,
		)

		aggregate_load