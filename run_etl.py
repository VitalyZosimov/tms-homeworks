#!/usr/bin/env python3

import subprocess
import sys
import os
from datetime import datetime


def run_script(script_name: str) -> bool:
#Запуск Python скрипта
		print(f"\n{'='*60}")
		print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
		print(f"Запуск: {script_name}")
		print(f"{'='*60}")

		result = subprocess.run([sys.executable, script_name], capture_output=False)
		return result.returncode == 0


def main():
#Запуск ETL пайплайна
		print("-.-.-" * 30)
		print("ЗАПУСК ETL ПАЙПЛАЙНА")
		print("-.-.-" * 30)

		start_time = datetime.now()

		if not run_script("extract_and_load.py"):
				print("Ошибка на этапе Extract & Load")
				sys.exit(1)

		if not run_script("transform_and_load.py"):
				print("Ошибка на этапе Transform & Load")
				sys.exit(1)

		end_time = datetime.now()
		duration = (end_time - start_time).total_seconds()

		print(".-.-" * 30)
		print(f"ETL ПАЙПЛАЙН ЗАВЕРШЕН!")
		print(f"Время: {duration:.2f} сек")
		print("-.-.-" * 30)


if __name__ == "__main__":
		main()