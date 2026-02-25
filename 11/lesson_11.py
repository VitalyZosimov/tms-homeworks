import functools
import datetime
import time

def log_calls(func):
    @functools.wraps(func)  # сохраняем имя
    def wrapper(*args, **kwargs):
        # Время вызова
        call_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Вызов оригинальной функции
        result = None
        try:
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            return result
        finally:
					
            # Запись 
            with open("function_log.txt", "a", encoding="utf-8") as file:
                file.write(
                    f"[{call_time}] "
                    f"Функция: {func.__name__}, "
                    f"Аргументы: args={args}, kwargs={kwargs}, "
                    f"Результат: {result}\n"
                    f"Время выполнения: {end_time - start_time}\n"
                )
    return wrapper
