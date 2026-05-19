import os
import pandas as pd

def generate_report(connection, report_dir="Reports", filename="report.csv"):
    try:
        root_dir = os.path.dirname(os.path.abspath(__file__))
        report_path = os.path.join(root_dir, report_dir)
        
        try:
            os.makedirs(report_path, exist_ok=True)
        except OSError as e:
            print(f"Ошибка создания папки {report_path}: {e}")
            return

        # Получаем список всех таблиц (для PostgreSQL)
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

        summary = []
        for table in tables:
            try:
                df = pd.read_sql(f'SELECT * FROM "{table}"', connection)
                summary.append({
                    "table": table,
                    "rows": len(df),
                    "columns": df.shape[1]
                })
                print(f" Обработана таблица {table}: {len(df)} строк, {df.shape[1]} колонок")
            except pd.errors.DatabaseError as e:
                print(f"❌ Ошибка чтения таблицы {table}: {e}")
                summary.append({
                    "table": table,
                    "rows": "Ошибка",
                    "columns": "Ошибка"
                })
            except Exception as e:
                print(f"❌ Непредвиденная ошибка при обработке таблицы {table}: {e}")

        try:
            report_df = pd.DataFrame(summary)
            file_path = os.path.join(report_path, filename)
            report_df.to_csv(file_path, index=False, encoding="utf-8")
            print(f"Отчёт сохранён в {file_path}")
        except PermissionError as e:
            print(f" Нет прав на запись файла {file_path}: {e}")
        except Exception as e:
            print(f" Ошибка сохранения отчёта: {e}")

    except Exception as e:
        print(f"Критическая ошибка в generate_report: {e}")
