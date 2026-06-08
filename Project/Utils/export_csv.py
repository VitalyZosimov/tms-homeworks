import os
import pandas as pd
import psycopg2

def export_to_csv(connection, export_dir="CSV/export"):
    try:
        # Определяем корневую папку проекта
        root_dir = os.path.dirname(os.path.abspath(__file__))
        export_path = os.path.join(root_dir, "..", export_dir)

        # Создаём папку, если её нет
        try:
            os.makedirs(export_path, exist_ok=True)
        except OSError as e:
            print(f" Ошибка создания папки {export_path}: {e}")
            return

        # Получаем список всех таблиц 
        try:
            query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
            """
            tables = pd.read_sql(query, connection)["table_name"].tolist()
        except Exception as e:
            print(f"Ошибка получения списка таблиц: {e}")
            return

        for table in tables:
            try:
                # Загружаем таблицу в DataFrame
                df = pd.read_sql(f'SELECT * FROM "{table}"', connection)

                # Формируем путь к файлу
                file_path = os.path.join(export_path, f"{table}.csv")

                # Сохраняем таблицу в отдельный CSV‑файл
                df.to_csv(file_path, index=False, encoding="utf-8")

                print(f" Таблица {table} сохранена в {file_path}")

            except pd.errors.DatabaseError as e:
                print(f"Ошибка чтения таблицы {table}: {e}")
            except PermissionError as e:
                print(f"Нет прав на запись файла {file_path}: {e}")
            except Exception as e:
                print(f" Непредвиденная ошибка при обработке таблицы {table}: {e}")

    except Exception as e:
        print(f" Критическая ошибка в export_to_csv: {e}")
