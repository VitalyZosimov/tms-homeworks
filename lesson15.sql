
-- Таблица Авторы
CREATE TABLE authors (
    author_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    birth_year INT,
    country VARCHAR(50),
    bio TEXT
);

-- Таблица Книги
CREATE TABLE books (
    book_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    year INT,
    author_id INT,
    genre_id INT,
    quantity INT,
    status VARCHAR(20),
    FOREIGN KEY (author_id) REFERENCES authors(author_id)
);

-- Таблица Читатели
CREATE TABLE readers (
    reader_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    ticket_number VARCHAR(20) UNIQUE,
    reg_date DATE DEFAULT CURRENT_DATE,
    phone VARCHAR(20),
    email VARCHAR(100)
);


INSERT INTO authors (full_name, birth_year, country, bio) VALUES
('Александр Пушкин', 1799, 'Россия', 'Русский поэт, драматург и прозаик.'),
('Джордж Оруэлл', 1903, 'Великобритания', 'Английский писатель и публицист.'),
('Фёдор Достоевский', 1821, 'Россия', 'Русский писатель, философ.');


INSERT INTO books (title, year, author_id, genre_id, quantity, status) VALUES
('Евгений Онегин', 1833, 1, 1, 5, 'доступна'),
('1984', 1949, 2, 2, 3, 'на руках'),
('Преступление и наказание', 1866, 3, 1, 4, 'доступна'),
('Стихотворения', 1830, 1, 3, 2, 'в ремонте');


INSERT INTO readers (full_name, ticket_number, phone, email) VALUES
('Иван Иванов', 'R001', '+375291234567', 'ivanov@example.com'),
('Мария Петрова', 'R002', '+375331112233', 'petrova@example.com'),
('Сергей Кузнецов', 'R003', '+375441234567', 'kuznetsov@example.com'),
('Анна Смирнова', 'R004', '+375251234567', 'smirnova@example.com');
