import os
import pandas as pd

def top_genres(
		input_dir="Utils/CSV/export",
		output_dir="results",
		filename="top5_genres.xlsx"
):
		root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
		input_path = os.path.join(root_dir, input_dir)
		output_path = os.path.join(root_dir, output_dir)
		os.makedirs(output_path, exist_ok=True)

		invoice_items = pd.read_csv(os.path.join(input_path, "invoice_items.csv"))
		tracks = pd.read_csv(os.path.join(input_path, "tracks.csv"))
		genres = pd.read_csv(os.path.join(input_path, "genres.csv"))

		merged = invoice_items.merge(tracks, on="TrackId", how="left")
		merged = merged.merge(genres, on="GenreId", how="left")

		# используем UnitPrice_x и Quantity
		merged["Revenue"] = merged["UnitPrice_x"] * merged["Quantity"]

		report = merged.groupby("Name_y")["Revenue"].sum().reset_index()
		report.rename(columns={"Name_y": "Genre", "Revenue": "TotalRevenue"}, inplace=True)

		top5 = report.sort_values(by="TotalRevenue", ascending=False).head(5)

		file_path = os.path.join(output_path, filename)
		top5.to_excel(file_path, index=False, engine="openpyxl")

		print(f"Топ-5 самых прибыльных жанров сохранён в {file_path}")
