from connect import get_connection
from Utils.export_excel import export_to_excel
from Utils.export_csv import export_to_csv
from report import generate_report

def main():
		conn = get_connection()

		# Экспорт в Excel
		export_to_excel(conn)

		# Экспорт в CSV
		export_to_csv(conn)

		# Генерация отчёта
		generate_report(conn)

		conn.close()
		print("Все операции завершены успешно!")

if __name__ == "__main__":
		main()
