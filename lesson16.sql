
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE
);

INSERT INTO users (full_name, email) VALUES
('Администратор', 'admin@example.com'),
('Маркетолог', 'marketer@example.com'),
('Менеджер', 'manager@example.com'),
('Оператор', 'operator@example.com');

CREATE TABLE promocodes (
    promo_id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    discount_percent INT CHECK (discount_percent BETWEEN 1 AND 100),
    valid_from DATE NOT NULL,
    valid_to DATE NOT NULL,
    max_uses INT DEFAULT NULL,
    used_count INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_by INT REFERENCES users(id)
);

INSERT INTO promocodes (code, discount_percent, valid_from, valid_to, max_uses, used_count, is_active, created_by) VALUES
('WELCOME5',   5,  '2026-01-01', '2026-12-31', NULL, 0, TRUE, 1),
('NEWYEAR20', 20,  '2025-12-01', '2026-01-15', 100, 25, FALSE, 2),
('SPRING15',  15,  '2026-03-01', '2026-05-31', 50, 10, TRUE, 1),
('SUMMER30',  30,  '2026-06-01', '2026-08-31', NULL, 0, TRUE, 3),
('BLACKFRIDAY50', 50, '2025-11-20', '2025-11-30', 500, 500, FALSE, 2),
('STUDENT10', 10,  '2026-02-01', '2026-12-31', NULL, 2, TRUE, 4),
('VIP25',     25,  '2026-01-01', '2026-12-31', 20, 5, TRUE, 1),
('AUTUMN40',  40,  '2025-09-01', '2025-11-30', 200, 150, FALSE, 3),
('FREESHIP',   5,  '2026-01-15', '2026-06-30', NULL, 0, TRUE, 2),
('LOYALTY35', 35,  '2026-02-01', '2026-12-31', 100, 10, TRUE, 4);