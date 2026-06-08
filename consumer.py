from confluent_kafka import Consumer
import json
import psycopg2
import time #Используем для задержек, иначе модуль не нужен
import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Читаем настройки PostgreSQL из переменных окружения
POSTGRES_CONFIG = {
	'host': os.getenv('POSTGRES_HOST', 'localhost'),
	'port': int(os.getenv('POSTGRES_PORT', 5432)),
	'dbname': os.getenv('POSTGRES_DB', 'events_db'),
	'user': os.getenv('POSTGRES_USER', 'user'),
	'password': os.getenv('POSTGRES_PASSWORD', 'password')
}

# Читаем настройки Kafka
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_GROUP_ID = os.getenv('KAFKA_GROUP_ID', 'user_events_group')
KAFKA_AUTO_OFFSET_RESET = os.getenv('KAFKA_AUTO_OFFSET_RESET', 'earliest')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'user_events')

# Подключение к PostgreSQL
conn = psycopg2.connect(**POSTGRES_CONFIG)
cursor = conn.cursor()

# Создание таблиц
cursor.execute("""
	CREATE TABLE IF NOT EXISTS login_events (
		id SERIAL PRIMARY KEY,
		user_id INTEGER NOT NULL,
		event_time TIMESTAMP NOT NULL,
		processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	)
""")
cursor.execute("""
	CREATE TABLE IF NOT EXISTS logout_events (
		id SERIAL PRIMARY KEY,
		user_id INTEGER NOT NULL,
		event_time TIMESTAMP NOT NULL,
		processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	)
""")
conn.commit()

# Конфигурация Kafka
kafka_conf = {
	'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
	'group.id': KAFKA_GROUP_ID,
	'auto.offset.reset': KAFKA_AUTO_OFFSET_RESET,
	'enable.auto.commit': False
}

consumer = Consumer(kafka_conf)
consumer.subscribe([KAFKA_TOPIC])

try:
	while True:
		msg = consumer.poll(1.0)

		if msg is None:
			continue
        
		if msg.error():
			print(f"Ошибка: {msg.error()}")
			continue

		event = json.loads(msg.value().decode('utf-8'))
		user_id = event['user_id']
		event_type = event['event']
		event_time = event['timestamp']

		if event_type == 'login':
			cursor.execute(
				"INSERT INTO login_events (user_id, event_time) VALUES (%s, %s)",
				(user_id, event_time)
			)
			print(f"Login: user {user_id}")

		elif event_type == 'logout':
			cursor.execute(
				"INSERT INTO logout_events (user_id, event_time) VALUES (%s, %s)",
				(user_id, event_time)
			)
			print(f"Logout: user {user_id}")

		else:
			print(f"Error: invalid event_type: {event_type}")

		conn.commit()
		consumer.commit(msg)

except KeyboardInterrupt:
	print("\nОстановлено ручным вводом")
finally:
	consumer.close()
	cursor.close()
	conn.close()