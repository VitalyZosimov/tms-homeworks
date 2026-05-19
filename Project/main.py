import sys
import os

# Добавляем путь к Utils для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from connect import get_connection
    from Utils.export_excel import export_to_excel
    from Utils.export_csv import export_to_csv
    from report import generate_report
except ImportError as e:
    print(f"Ошибка импорта модулей: {e}")
    print("Проверьте структуру папок и наличие всех файлов")
    sys.exit(1)

def main():
    print("Запуск ETL процесса...")
    
    # Подключение к базе данных
    try:
        conn = get_connection()
        if conn is None:
            print("❌ Не удалось подключиться к базе данных")
            return
        print("Подключение к БД установлено")
    except Exception as e:
        print(f"Ошибка при подключении к БД: {e}")
        return

    try:
        # Экспорт в Excel
        print("\n Экспорт в Excel...")
        export_to_excel(conn)

        # Экспорт в CSV
        print("\n Экспорт в CSV...")
        export_to_csv(conn)

        # Генерация отчёта
        print("\n Генерация отчёта...")
        generate_report(conn)

        print("\n Все операции завершены успешно!")

    except Exception as e:
        print(f"\n Ошибка во время выполнения операций: {e}")
    finally:
        try:
            conn.close()
            print("Соединение с БД закрыто")
        except Exception as e:
            print(f"Ошибка при закрытии соединения: {e}")

if __name__ == "__main__":
    main()
