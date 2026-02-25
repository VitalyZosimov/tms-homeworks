
import sqlite3
import pandas as pd

connection = sqlite3.connect("database.db")
cursor = connection.cursor()

# Средний возраст клиентов из Минска
data_frame = pd.read_sql_query('SELECT AVG(age) FROM clients WHERE city = "Минск"', connection)
print(f"Средний возраст клиентов из города Минск\n{data_frame}")

# Клиенты с балансом более 1000
data_frame = pd.read_sql_query('SELECT c.name, b.amount FROM clients c JOIN balance b ON c.client_id = b.client_id WHERE b.amount > 1000', connection)
print(f"Клиенты с балансом более 1000\n{data_frame}")

# Количество операций по типу транзакций
data_frame = pd.read_sql_query('SELECT t.type,COUNT(t.transaction_id) FROM transactions t GROUP BY t.type', connection)
print(f"Количество операций по типу транзакций\n{data_frame}")

# Топ 3 клиента по количеству транзакций
data_frame = pd.read_sql_query('SELECT c.name, COUNT(t.transaction_id) as count FROM transactions t RIGHT JOIN clients c ON t.client_id = c.client_id GROUP BY c.name ORDER BY count DESC LIMIT 3', connection)
print(f"Топ 3 клиента по количеству транзакций\n{data_frame}")

# Клиенты с наибольшими расходами
data_frame = pd.read_sql_query('SELECT c.name, SUM(t.amount) as sum FROM transactions t RIGHT JOIN clients c ON t.client_id = c.client_id WHERE t.amount < 0 GROUP BY c.name ORDER BY sum', connection)
print(f"Клиенты с наибольшими расходами\n{data_frame}")

# Выявление подозрительных операций
sus_percent = float(input("Введите процент: "))
data_frame = pd.read_sql_query(f'SELECT t.amount as payment_amount, b.amount as balance, t.description FROM transactions t RIGHT JOIN balance b ON t.client_id = b.client_id WHERE t.amount > b.amount * {sus_percent}/100',connection)
print(f"Подозрительные операции (сумма которых превышает {sus_percent}% от баланса)\n{data_frame}")
