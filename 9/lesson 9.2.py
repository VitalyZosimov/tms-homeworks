
class Student:
    def __init__(self, name, group, grades=None, average=None):
        self.name = name
        self.group = group
        self.grades = grades
        self.average = average

    def __str__(self):
        return f"ФИО: {self.name} -- Группа: {self.group} -- Оценки: {self.grades} -- Средняя оценка: {self.average}"
    
    def __repr__(self):
        return self.__str__()


grades_file = "grades.txt"
students_file = "students.txt"
output_file = "report.txt"

students_groups = {}
students_grades = {}
students = {}
group_grades = {}

with open(students_file, "r", encoding="utf-8") as file:
    for line in file:
        part = line.strip().split(", ")
        student_name = part[0]
        student_group = part[1]
        # students_groups[student_name] = student_group
        students[student_name] = Student(student_name, student_group)

with open(grades_file, "r", encoding="utf-8") as file:
    for line in file:
        part = line.strip().split(", ")
        student_name = part[0]
        student_grades = part[1]
        student_grades_list = list(map(int,student_grades.split(" ")))
        students[student_name].grades = student_grades_list
        students[student_name].average = sum(student_grades_list) / len(student_grades_list)

# {Группа : [Сумма оценок, количество человек в группе]}
for fio, student in students.items():
    if student.group in group_grades:
        group_grades[student.group][0] = group_grades[student.group][0] + student.average
        group_grades[student.group][1] += 1
    else:
        group_grades[student.group] = [student.average, 1]

group_avgs = {group: total / count for group, (total, count) in group_grades.items()}
sorted_groups = sorted(group_avgs.items(), key=lambda x: x[1])

print(students)
with open(output_file, "w", encoding="utf-8") as file:
    for fio, student in students.items():
        file.write(f"{student.name}, {student.group}, {student.grades}, Средняя оценка: {student.average}\n")

    file.write(f"Средняя оценка по группам: \n")
    for group_name, average_by_group in sorted_groups:
        file.write(f"{group_name} : {average_by_group}\n")