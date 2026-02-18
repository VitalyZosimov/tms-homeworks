from lesson_11 import log_calls
import time

@log_calls
def safe_calculator(a, b, operation):
    time.sleep(2)
    try:
        # Попытка преобразовать входные данные в числа
        a = float(a)
        b = float(b)

        # Словарь доступных операций
        operations = {
            "+": lambda x, y: x + y,
            "-": lambda x, y: x - y,
            "*": lambda x, y: x * y,
            "/": lambda x, y: x / y
        }

        if operation not in operations:
            raise ValueError("Неподдерживаемая операция")

        return operations[operation](a, b)

    except ZeroDivisionError:
        return "Ошибка: деление на ноль"
    except ValueError as e:
        return f"Ошибка: {e}"
    except Exception:
        return "Ошибка: неверный тип данных"
print(safe_calculator(10, 5, "+"))    # 15.0
print(safe_calculator("10", "2", "*")) # 20.0 (строки преобразуются в числа)
print(safe_calculator(10, 0, "/"))    # Ошибка: деление на ноль
print(safe_calculator(10, 5, "^"))    # Ошибка: Неподдерживаемая операция
print(safe_calculator("abc", 5, "+")) # Ошибка: неверный тип данных
