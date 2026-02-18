
import requests

capsules = requests.get("https://api.spacexdata.com/v3/capsules").json()

# Количество капсул разного типа
counts = {}
for c in capsules:
    ctype = c['type']
    counts[ctype] = counts.get(ctype, 0) + 1

print("Количество капсул каждого типа:")
for ctype, count in counts.items():
    print(f"{ctype}: {count}")

# Капсулы без инофрмации о запуске
no_info = [c['capsule_serial'] for c in capsules if c['original_launch'] is None]
print(f"Капсулы без инфо о запуске: {no_info}")
