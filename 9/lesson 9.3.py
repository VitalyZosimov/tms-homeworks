def update_balances(accounts_file, transactions_file, output_file):
    balances = {}

    # 1. Читаем текущие балансы в словарь
    try:
        with open(accounts_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    name, amount = line.strip().split(':')
                    balances[name] = float(amount)
    except FileNotFoundError:
        print(f"Файл {accounts_file} не найден.")
        return

    # 2. Применяем транзакции
    try:
        with open(transactions_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    name, amount = line.strip().split(':')
                    change = float(amount)
                    
                    # Обновляем баланс (если имени нет в базе, создаем новое)
                    balances[name] = balances.get(name, 0) + change
    except FileNotFoundError:
        print(f"Файл {transactions_file} не найден.")
        return

    # 3. Сохраняем результат в новый файл
    with open(output_file, 'w', encoding='utf-8') as f:
        for name, balance in balances.items():
            f.write(f"{name}:{balance}\n")
    
    print(f"Данные успешно обновлены и сохранены в {output_file}")

# Запуск функции
update_balances('accounts.txt', 'transactions.txt', 'updated_accounts.txt')
