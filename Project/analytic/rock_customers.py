import os
import pandas as pd

def rock_customers(
		input_dir="Utils/CSV/export",
		output_dir="results",
		filename="top_rock_customers.xlsx"
):
		root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
		input_path = os.path.join(root_dir, input_dir)
		output_path = os.path.join(root_dir, output_dir)
		os.makedirs(output_path, exist_ok=True)

		# Загружаем таблицы
		customers = pd.read_csv(os.path.join(input_path, "customers.csv"))
		invoices = pd.read_csv(os.path.join(input_path, "invoices.csv"))
		invoice_items = pd.read_csv(os.path.join(input_path, "invoice_items.csv"))
		tracks = pd.read_csv(os.path.join(input_path, "tracks.csv"))
		genres = pd.read_csv(os.path.join(input_path, "genres.csv"))

		# Объединяем
		merged = customers.merge(invoices, on="CustomerId", how="left")
		merged = merged.merge(invoice_items, on="InvoiceId", how="left")
		merged = merged.merge(tracks, on="TrackId", how="left")
		merged = merged.merge(genres, on="GenreId", how="left")

		# Фильтруем только Rock
		rock_sales = merged[merged["Name_y"] == "Rock"]

		# Считаем количество купленных треков
		report = rock_sales.groupby(["CustomerId", "FirstName", "LastName"])["Quantity"].sum().reset_index()
		report.rename(columns={"Quantity": "TotalRockTracks"}, inplace=True)

		# Сортируем по убыванию
		top_customers = report.sort_values(by="TotalRockTracks", ascending=False)

		# Сохраняем в Excel
		file_path = os.path.join(output_path, filename)
		top_customers.to_excel(file_path, index=False, engine="openpyxl")

		print(f"Топ клиентов по покупкам жанра Rock сохранён в {file_path}")
