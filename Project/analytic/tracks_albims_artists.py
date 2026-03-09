import os
import pandas as pd

def merge_tracks_albums_artists(
		input_dir="Utils/CSV/export",
		output_dir="results",
		filename="tracks_albums_artists.xlsx"
):
		root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
		input_path = os.path.join(root_dir, input_dir)
		output_path = os.path.join(root_dir, output_dir)
		os.makedirs(output_path, exist_ok=True)

		#Загружаем из таблицы
		tracks = pd.read_csv(os.path.join(input_path, "tracks.csv"))
		albums = pd.read_csv(os.path.join(input_path, "albums.csv"))
		artists = pd.read_csv(os.path.join(input_path, "artists.csv"))

		#объединяе tracks и albims -> добавляем название альбома
		merged = tracks.merge(albums, on="AlbumId", how="left")

		#объединяем merge и artists -> добавляем имя певца
		merged = merged.merge(artists, on="ArtistId", how="left")

		#оставляем необходимые колонки
		result = merged[["TrackId", "Name_x", "Title", "Name_y"]].copy()
		result.rename(columns={
			"Name_x": "TrackName",
			"Title": "AlbumTitle",
			"Name_y": "ArtistName"
		}, inplace=True)

		#Сохраняем
		file_path = os.path.join(output_path, filename)
		result.to_excel(file_path, index=False, engine="openpyxl")

		print(f"Список треков, альбомов и артиста сохранен в {file_path}")
