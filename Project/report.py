import os
import pandas as pd

def generate_report(connection, report_dir="Reports", filename="report.csv"):
		root_dir = os.path.dirname(os.path.abspath(__file__))
		report_path = os.path.join(root_dir, report_dir)
		os.makedirs(report_path, exist_ok=True)

		tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", connection)["name"].tolist()

		summary = []
		for table in tables:
			df = pd.read_sql(f"SELECT * FROM {table}", connection)
			summary.append({
					"table": table,
					"rows": len(df),
					"columns": df.shape[1]
				})

		report_df = pd.DataFrame(summary)
		file_path = os.path.join(report_path, filename)
		report_df.to_csv(file_path, index=False, encoding="utf-8")

		print(f"Отчёт сохранён в {file_path}")
