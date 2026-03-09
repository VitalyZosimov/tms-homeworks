import os
import pandas as pd

def calculate_avg_duration(
		input_dir="Utils/CSV/export",
		output_dir="results",
		filename="avg_duration.xlsx"
):
		root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
		input_path = os.path.join(root_dir, input_dir)
		output_path = os.path.join(root_dir, output_dir)
		os.makedirs(output_path, exist_ok=True)

		tracks = pd.read_csv(os.path.join(input_path, "tracks.csv"))
		genres = pd.read_csv(os.path.join(input_path, "genres.csv"))

		merged = tracks.merge(genres, on="GenreId")

		#Используем name_y как колонку жанра
		if "Name_y"not in merged.columns:
			raise ValueError(f"В объединённых данных нет колонки 'Name_y'. Доступные: {merged.columns.tolist()}")

		report = merged.groupby("Name_y")["Milliseconds"].mean().reset_index()
		report.rename(columns={"Name_y": "Genre", "Milliseconds": "AvgDuration_ms"}, inplace=True)

		#Сохраняем
		file_path = os.path.join(output_path, filename)
		report.to_excel(file_path, index=False, engine="openpyxl")

		print(f"Отчёт по средней длительности треков сохранён в {file_path}")
