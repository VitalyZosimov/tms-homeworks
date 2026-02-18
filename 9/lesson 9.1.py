

input_file = "filename.txt"
output_file = "statistics.txt"

professions = {}
cities = {}
countries = {}

with open(input_file, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.strip().split(", ")
        if len(parts) < 8:
            continue

        profession = parts[5]
        city = parts[6]
        country = parts[7]

        if profession in professions:
            professions[profession] += 1
        else:
            professions[profession] = 1

        if city in cities:
            cities[city] += 1
        else:
            cities[city] = 1

        if country in countries:
            countries[country] += 1
        else:
            countries[country] = 1

with open(output_file, "w", encoding="utf-8") as f:
    f.write("Статистика по профессиям:\n")
    for profession, count in professions.items():
        f.write(f"{profession}: {count} человек\n")

    f.write("Статистика по городам:\n")
    for city, count in cities.items():
        f.write(f"{city}: {count} человек\n")

    f.write("Статистика по странам:\n")
    for country, count in countries.items():
        f.write(f"{country}: {count} человек\n")