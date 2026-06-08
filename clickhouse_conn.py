import clickhouse_connect
import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

def get_clickhouse_config():

	config = {
		'host': os.getenv('CLICKHOUSE_HOST'),
		'port': os.getenv('CLICKHOUSE_PORT'),
		'username': os.getenv('CLICKHOUSE_USERNAME'),
		'password': os.getenv('CLICKHOUSE_PASSWORD'),
		'database': os.getenv('CLICKHOUSE_DATABASE')
	}

# Проверка обязательных параметров
	if not config['host']:
		raise ValueError("CLICKHOUSE_HOST не задан в .env файле")

# Преобразование порта в int
	if config['port']:
		config['port'] = int(config['port'])
	else:
		config['port'] = 8123  # порт по умолчанию

# Значения по умолчанию для остальных параметров
		config['username'] = config['username'] or 'default'
		config['password'] = config['password'] or ''
		config['database'] = config['database'] or 'default'

	return config

try:
# Получаем конфигурацию
	config = get_clickhouse_config()

# Подключаемся к ClickHouse
	client = clickhouse_connect.get_client(**config)

	print(f"Подключено к ClickHouse: {config['host']}:{config['port']}")

# Запрос
	query = "SELECT name, database, engine FROM system.tables LIMIT 10"
	result = client.query(query)

	print("\n Результат запроса:")
	print("-" * 50)
	for row in result.result_rows:
		print(f"  Таблица: {row[0]}, База: {row[1]}, Движок: {row[2]}")
	print("-" * 50)

except Exception as e:
	print(f"Ошибка: {e}")
finally:
	if 'client' in locals():
		client.close()
		print("\nСоединение закрыто")