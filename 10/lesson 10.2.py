# Открываем исходный файл для чтения и новый файл для записи очищенных данных
with open("raw_data.txt", "r", encoding="utf-8") as raw_file:
	with open("cleaned_data.txt", "w", encoding="utf-8") as file:
		# Построчно обрабатываем входящий файл
		for line in raw_file:
				line = line.strip()	# Убираем лишние пробелы и символы переноса строки

				 # Пропускаем строки, содержащие ошибку (фильтрация мусора)
				if "ERROR" in line:
					continue
				
				# Разбираем строку на части, используя двоеточие как разделитель
				date, amount, manager = line.strip().split(":")
				
				 # Записываем данные в новый файл, меняя формат на CSV (разделение запятыми)
				file.write(f"{date},{amount},{manager}\n")