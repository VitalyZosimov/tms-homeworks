import os
import pandas as pd

def export_to_csv(connection, export_dir="CSV/export"):
		# Определяем корневую папку проекта
		root_dir = os.path.dirname(os.path.abspath(__file__))
		export_path = os.path.join(root_dir, "..", export_dir)

		# Создаём папку, если её нет
		os.makedirs(export_path, exist_ok=True)

		# Получаем список всех таблиц
		tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", connection)["name"].tolist()

		for table in tables:
			# Загружаем таблицу в DataFrame
			df = pd.read_sql(f"SELECT * FROM {table}", connection)

			# Формируем путь к файлу
			file_path = os.path.join(export_path, f"{table}.csv")

			# Сохраняем таблицу в отдельный CSV‑файл
			df.to_csv(file_path, index=False, encoding="utf-8")

		print(f"Таблица {table} сохранена в {file_path}")
