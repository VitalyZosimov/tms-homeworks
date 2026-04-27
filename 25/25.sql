
CREATE TABLE IF NOT EXISTS departments (
    department_id SERIAL PRIMARY KEY,
    department_name VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS teachers (
    teacher_id SERIAL PRIMARY KEY,
    teacher_name VARCHAR(100) NOT NULL,
    department_id INTEGER NOT NULL REFERENCES departments(department_id) ON DELETE RESTRICT
);


CREATE TABLE IF NOT EXISTS courses (
    course_id INTEGER PRIMARY KEY,
    course_name VARCHAR(100) NOT NULL,
    teacher_id INTEGER NOT NULL REFERENCES teachers(teacher_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY,
    student_name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS grades (
    course_id INTEGER REFERENCES courses(course_id) ON DELETE CASCADE,
    student_id INTEGER REFERENCES students(student_id) ON DELETE CASCADE,
    grade INTEGER NOT NULL CHECK (grade >= 0 AND grade <= 5),
    PRIMARY KEY (course_id, student_id)
);


INSERT INTO departments (department_name, phone) VALUES
('Математики', '+7 495 123-45-67'),
('Истории', '+7 495 765-43-21')
ON CONFLICT (department_name) DO NOTHING;

INSERT INTO teachers (teacher_name, department_id) VALUES
('Петров', (SELECT department_id FROM departments WHERE department_name = 'Математики')),
('Сидорова', (SELECT department_id FROM departments WHERE department_name = 'Истории'));

INSERT INTO courses (course_id, course_name, teacher_id) VALUES
(1, 'Математика', (SELECT teacher_id FROM teachers WHERE teacher_name = 'Петров')),
(2, 'История', (SELECT teacher_id FROM teachers WHERE teacher_name = 'Сидорова'));

INSERT INTO students (student_id, student_name) VALUES
(101, 'Иван'),
(102, 'Мария');

INSERT INTO grades (course_id, student_id, grade) VALUES
(1, 101, 5),
(1, 102, 4),
(2, 101, 4);

