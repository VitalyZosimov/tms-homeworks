data = {
		"data_2023_01.txt": [
				"2023-01-01:1000:Иван Иванов",
				"2023-01-02:1500:Петр Петров",
				"2023-01-02:2000:Мария Сидорова",
		],
		"data_2023_02.txt": [
				"2023-02-01:2000:Иван Иванов",
				"2023-02-02:1800:Петр Петров",
				"2023-02-03:2200:Мария Сидорова",
		],
		"data_2023_03.txt": [
				"2023-03-01:2100:Мария Сидорова",
				"2023-03-02:1300:Иван Иванов",
				"2023-03-03:1700:Петр Петров",
		]
}

# Создание физических файлов на диске на основе словаря data
for filename, lines in data.items():
		with open(f"{filename}", "w", encoding="utf-8") as file:
			for line in lines:
				file.write(line + "\n")

# Инициализация переменных для хранения агрегированных данных
manager_sales = {}	# Словарь для накопления суммы продаж по каждому менеджеру
total_sales = 0			# Переменная для подсчета общей суммы всех продаж

# Чтение созданных файлов и обработка данных
for date_file in data:
		with open(f"{date_file}", "r", encoding="utf-8") as file:
			for line in file:
				# Разделение строки по двоеточию на компоненты
				date, amount, manager = line.strip().split(":")
				amount = int(amount)	# Преобразование суммы в число
				total_sales += amount	# Прибавляем к общей сумме

# Обновление суммы продаж конкретного менеджера в словаре
			if manager not in manager_sales:
				manager_sales[manager] = 0
				manager_sales[manager] += amount

            # print(manager_sales.items())

# Определение менеджера с максимальной суммой продаж
# max() ищет ключ с наибольшим значением, используя manager_sales.get как критерий
			best_manager = max(manager_sales,key=manager_sales.get)
			best_manager_sales = manager_sales[best_manager]

# Запись итогового отчета в файл report.txt
with open("report.txt", "w", encoding="utf-8") as file:
		file.write(f"Общая сумма продаж: {total_sales}\nЛучший менеджер: {best_manager}\nЛучшая сумма продаж: {best_manager_sales}")