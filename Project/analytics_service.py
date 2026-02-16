from analytic.avg_duration import calculate_avg_duration
from analytic.tracks_albims_artists import merge_tracks_albums_artists
from analytic.Top5 import top_genres
from analytic.rock_customers import rock_customers

def run_analytics():
		# Средняя длительность
		calculate_avg_duration()

		#объединяем разные таблицы
		merge_tracks_albums_artists()

		# Топ 5 прибыльных жанров
		top_genres()

		# Топ клиентов по покупке жанра Рок
		rock_customers()

		print("Все аналитические расчёты завершены!")

if __name__ == "__main__":
		run_analytics()
