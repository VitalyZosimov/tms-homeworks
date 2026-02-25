import pandas as pd
import numpy as np

data_frame = pd.read_csv("hw_DE_12.csv")

# Все женщины с IP адресом, начинающимся на 1
print("Все женщины с IP адресом, начинающимся на 1")
print(data_frame[(data_frame["gender"] == "Female") & (data_frame["ip_address"].str[0] == "1")])

# Новый столбец с доменами из электронных почт
print("Новый столбец с доменами из электронных почт")
data_frame["domain"] = data_frame["email"].apply(lambda x: x.split("@")[1])
print(data_frame)

# Уникальные domain (переведённые в list)
print("Уникальные domain (переведённые в list)")
print(data_frame["domain"].unique().tolist())

# Анализ возраста
print("Анализ возраста")
data_frame["age"] = np.random.randint(16,65,size=len(data_frame))
groups = [18, 25, 35, 50, 100]
values = ["18-25", "26-35", "36-50", "51+"]    
data_frame["age_group"] = pd.cut(data_frame["age"], bins=groups, labels=values)
print(data_frame)