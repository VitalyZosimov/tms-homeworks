# dags/producer_dag.py
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.datasets import Dataset
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.mongo.hooks.mongo import MongoHook
from airflow.models.baseoperator import chain
import logging
from typing import List, Dict, Any
from pydantic import ValidationError

import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent.parent))
from models.ticket_schemas import SupportTicket

# Настройка логгера
logger = logging.getLogger(__name__)

# Определяем Dataset для передачи между DAG'ами
SUPPORT_TICKETS_DATASET = Dataset("postgres://stg_hw41_support_valid_tickets")

# SQL для создания таблицы в PostgreSQL
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS stg_hw41_support_valid_tickets (
		ticket_id TEXT PRIMARY KEY,
		user_id TEXT NOT NULL,
		priority TEXT NOT NULL,
		category TEXT NOT NULL,
		resolution_minutes INTEGER NOT NULL,
		channel TEXT NOT NULL,
		created_at TIMESTAMPTZ NOT NULL,
		loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

# SQL для UPSERT
UPSERT_SQL = """
INSERT INTO stg_hw41_support_valid_tickets 
		(ticket_id, user_id, priority, category, resolution_minutes, channel, created_at, loaded_at)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (ticket_id) 
DO UPDATE SET
		user_id = EXCLUDED.user_id,
		priority = EXCLUDED.priority,
		category = EXCLUDED.category,
		resolution_minutes = EXCLUDED.resolution_minutes,
		channel = EXCLUDED.channel,
		created_at = EXCLUDED.created_at,
		loaded_at = NOW();
"""

def read_from_mongo(**context):
	"""Чтение сообщений из MongoDB за текущий data_interval"""
	mongo_hook = MongoHook(mongo_conn_id='mongo_default')
	postgres_hook = PostgresHook(postgres_conn_id='postgres_default')

# Получаем окно выполнения из контекста Airflow
	data_interval_start = context['data_interval_start']
	data_interval_end = context['data_interval_end']

	logger.info(f"📖 Чтение данных за период: {data_interval_start} - {data_interval_end}")

# Подключаемся к MongoDB
	client = mongo_hook.get_conn()
	db = client['source_db']
	collection = db['support_tickets_stream']

# Фильтр по created_at
	query = {
		"created_at": {
			"$gte": data_interval_start.isoformat(),
			"$lt": data_interval_end.isoformat()
		}
	}

# Читаем документы
	cursor = collection.find(query)
	tickets = list(cursor)

	logger.info(f"📊 Найдено {len(tickets)} документов в MongoDB")

# Создаем таблицу если не существует
	postgres_hook.run(CREATE_TABLE_SQL)

# Валидация и вставка
	valid_count = 0
	invalid_count = 0

	for ticket in tickets:
# Убираем _id из MongoDB
			ticket.pop('_id', None)

			try:
# Валидация через Pydantic
				validated_ticket = SupportTicket(**ticket)

# Подготовка данных для PostgreSQL
				row_data = (
					validated_ticket.ticket_id,
					validated_ticket.user_id,
					validated_ticket.priority,
					validated_ticket.category,
					validated_ticket.resolution_minutes,
					validated_ticket.channel,
					validated_ticket.created_at,
					datetime.now()
				)

# UPSERT в PostgreSQL
				postgres_hook.run(UPSERT_SQL, parameters=row_data)
				valid_count += 1
				logger.info(f"Валидный тикет {validated_ticket.ticket_id} сохранен")

			except ValidationError as e:
				logger.warning(f"Невалидный тикет {ticket.get('ticket_id', 'unknown')}: {e.errors()}")
				invalid_count += 1
			except Exception as e:
				logger.error(f"Ошибка при обработке тикета {ticket.get('ticket_id', 'unknown')}: {e}")
				invalid_count += 1

	client.close()

	logger.info(f"🎯 Обработка завершена. Валидных: {valid_count}, Невалидных: {invalid_count}")

# Сохраняем статистику в XCom
	context['ti'].xcom_push(key='processing_stats', value={
		'valid_count': valid_count,
		'invalid_count': invalid_count,
		'window_start': data_interval_start.isoformat(),
		'window_end': data_interval_end.isoformat()
	})

	return valid_count, invalid_count


# Определение DAG
default_args = {
		'owner': 'airflow',
		'depends_on_past': False,
		'start_date': datetime(2026, 1, 1),
		'email_on_failure': False,
		'email_on_retry': False,
		'retries': 1,
		'retry_delay': timedelta(minutes=5),
}

with DAG(
		'support_tickets_producer',
		default_args=default_args,
		description='Producer DAG: Mongo -> Postgres',
		schedule=timedelta(hours=1),
		catchup=False,
		tags=['etl', 'producer'],
) as dag:

	process_tickets = PythonOperator(
		task_id='process_tickets_from_mongo',
		python_callable=read_from_mongo,
		outlets=[SUPPORT_TICKETS_DATASET],
		)

	process_tickets