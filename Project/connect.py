import psycopg2
import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

def get_connection():

    config = {
        'host': os.getenv('PG_HOST', 'localhost'),
        'port': os.getenv('PG_PORT', '5432'),
        'database': os.getenv('PG_DATABASE', 'raw_data'),
        'user': os.getenv('PG_USER', 'etl_user'),
        'password': os.getenv('PG_PASSWORD', '123')
    }
    
    try:
        conn = psycopg2.connect(**config)
        print(f"Успешное подключение к PostgreSQL: {config['host']}:{config['port']}/{config['database']}")
        return conn
    except psycopg2.OperationalError as e:
        print(f"Ошибка подключения к PostgreSQL: {e}")
        print(f"Проверьте, запущен ли PostgreSQL и правильность настроек")
        return None
    except psycopg2.Error as e:
        print(f"Ошибка PostgreSQL: {e}")
        return None
    except Exception as e:
        print(f"Непредвиденная ошибка: {e}")
        return None
