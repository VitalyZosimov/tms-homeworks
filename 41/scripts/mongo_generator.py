# scripts/mongo_generator.py
import random
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Конфигурация
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "source_db"
COLLECTION_NAME = "support_tickets_stream"

# Валидные значения
VALID_PRIORITIES = ["low", "medium", "high", "urgent"]
VALID_CATEGORIES = ["payment", "delivery", "technical", "account"]
VALID_CHANNELS = ["chat", "email", "phone"]

# Невалидные значения для инъекции ошибок
INVALID_PRIORITIES = ["critical", "very_high", "low_medium"]
INVALID_RESOLUTIONS = [-5, -1, 0, 10000]


def generate_valid_ticket(ticket_num: int, base_date: datetime) -> Dict[str, Any]:
	"""Генерация валидного тикета"""
	return {
				"ticket_id": f"TCKT-2026-{ticket_num:06d}",
				"user_id": f"u_{random.randint(1000, 9999)}",
				"priority": random.choice(VALID_PRIORITIES),
				"category": random.choice(VALID_CATEGORIES),
				"resolution_minutes": random.randint(1, 300),
				"channel": random.choice(VALID_CHANNELS),
				"created_at": (base_date + timedelta(minutes=random.randint(0, 1440))).isoformat() + "Z"
	}


def generate_invalid_ticket(ticket_num: int, base_date: datetime) -> Dict[str, Any]:
	"""Генерация невалидного тикета с разными типами ошибок"""
	ticket = generate_valid_ticket(ticket_num, base_date)

	error_type = random.choice(["priority", "resolution", "both"])

	if error_type in ["priority", "both"]:
		ticket["priority"] = random.choice(INVALID_PRIORITIES)

		if error_type in ["resolution", "both"]:
			ticket["resolution_minutes"] = random.choice(INVALID_RESOLUTIONS)

	return ticket


def generate_test_data(total_docs: int = 200) -> List[Dict[str, Any]]:
	"""Генерация тестовых данных с 10-20% невалидных записей"""
	invalid_percentage = random.uniform(10, 20)
	invalid_count = int(total_docs * invalid_percentage / 100)
	valid_count = total_docs - invalid_count

	# Базовая дата - последние 7 дней
	base_date = datetime.now() - timedelta(days=7)

	tickets = []

	# Генерация валидных тикетов
	for i in range(valid_count):
			tickets.append(generate_valid_ticket(i + 1, base_date))

	# Генерация невалидных тикетов
	for i in range(invalid_count):
			tickets.append(generate_invalid_ticket(valid_count + i + 1, base_date))

	# Перемешиваем
	random.shuffle(tickets)

	return tickets


def insert_to_mongo(tickets: List[Dict[str, Any]]):
	"""Вставка данных в MongoDB"""
	try:
		client = MongoClient(MONGO_URI)
		db = client[DATABASE_NAME]
		collection = db[COLLECTION_NAME]

	# Очищаем коллекцию перед вставкой
		collection.delete_many({})

	# Вставляем документы
		result = collection.insert_many(tickets)

		print(f"Успешно вставлено {len(result.inserted_ids)} документов в MongoDB")
		print(f"Коллекция: {DATABASE_NAME}.{COLLECTION_NAME}")

	# Статистика
		valid_count = sum(1 for t in tickets 
											if t["priority"] in VALID_PRIORITIES 
											and isinstance(t["resolution_minutes"], int) 
											and t["resolution_minutes"] > 0)
		invalid_count = len(tickets) - valid_count

		print(f"Валидных: {valid_count}")
		print(f"Невалидных: {invalid_count} ({invalid_count/len(tickets)*100:.1f}%)")

		client.close()

	except ConnectionFailure as e:
			print(f"Ошибка подключения к MongoDB: {e}")
	raise


def main():
	"""Основная функция"""
	print("Запуск генератора тестовых данных")

	# Генерируем от 100 до 300 документов
	total_docs = random.randint(100, 300)
	print(f"Всего документов для генерации: {total_docs}")

	tickets = generate_test_data(total_docs)
	insert_to_mongo(tickets)

print("Генерация завершена!")


if __name__ == "__main__":
	main()