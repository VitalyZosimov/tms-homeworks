-- Задача 1: Создание таблицы с первичным ключом
--Создайте новую таблицу Airlines (авиакомпании), которая будет хранить информацию об авиакомпаниях. Записать данные туда рандомные.
--Таблица должна содержать следующие поля:
--- airline_id (идентификатор авиакомпании, целое число, уникальное значение).
--- airline_name (название авиакомпании, строка).
--- country (страна регистрации авиакомпании, строка).
--- Обеспечьте уникальность airline_id !


--Задача 2: Добавление внешнего ключа
--Добавьте поле airline_id в таблицу Flights, чтобы связать каждый рейс с авиакомпанией. 
--Создайте внешний ключ на это поле, ссылающийся на таблицу Airlines.


--Задача 3: Частичный индекс для отмененных рейсов
--Добавьте поле is_cancelled (логическое значение) в таблицу Flights. 
--Создайте частичный индекс для ускорения поиска только отмененных рейсов. 
--Сравните результаты до и после создания индекса

--Задача 4: Составной индекс для поиска билетов
--Создайте составной индекс для ускорения поиска билетов (Tickets) по имени пассажира и номеру билета. Сравните результаты до и после создания индекса.


--Задача 5*: Оптимизация JOIN-запроса между рейсами и аэропортами
--В таблице Flights хранится информация о рейсах, а в таблице Airports — информация об аэропортах. Вы часто выполняете запрос на получение всех рейсов из определенного аэропорта:
--EXPLAIN ANALYZE
--SELECT f.flight_id, f.flight_no, a.airport_name
--FROM bookings.flights f
--JOIN bookings.airports a ON f.departure_airport = a.airport_code
--WHERE a.airport_name = 'Домодедово';
--Создайте индекс для ускорения этого запроса.



-- Задание 1
CREATE TABLE Airlines (
    airline_id INTEGER PRIMARY KEY,
    airline_name VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL
);


INSERT INTO Airlines (airline_id, airline_name, country) VALUES
(1, 'Aeroflot', 'Russia'),
(2, 'S7 Airlines', 'Russia'),
(3, 'Utair', 'Russia'),
(4, 'Pobeda', 'Russia'),
(5, 'Turkish Airlines', 'Turkey'),
(6, 'Emirates', 'UAE'),
(7, 'Lufthansa', 'Germany'),
(8, 'Air France', 'France'),
(9, 'British Airways', 'UK'),
(10, 'Qatar Airways', 'Qatar');


SELECT airline_id, airline_name FROM Airlines ORDER BY airline_id;
-- END


-- Задание 2
ALTER TABLE flights ADD COLUMN airline_id INTEGER;
ALTER TABLE flights 
ADD CONSTRAINT fk_flights_airlines 
FOREIGN KEY (airline_id) REFERENCES Airlines(airline_id);
-- END


-- Задание 3 
ALTER TABLE flights ADD COLUMN is_cancelled BOOLEAN DEFAULT FALSE;

UPDATE flights 
SET is_cancelled = (random() < 0.05);

SELECT is_cancelled, COUNT(*) FROM flights GROUP BY is_cancelled;

EXPLAIN ANALYZE 
SELECT * FROM flights WHERE is_cancelled = TRUE;

CREATE INDEX idx_flights_cancelled ON flights (is_cancelled) 
WHERE is_cancelled = TRUE;

EXPLAIN ANALYZE 
SELECT * FROM flights WHERE is_cancelled = TRUE;
-- END


-- Задание 4
EXPLAIN ANALYZE 
SELECT * FROM tickets 
WHERE passenger_name = 'VALENTINA AKIMOVA' AND ticket_no = '0005432000370';

CREATE INDEX idx_tickets_name_number ON tickets (passenger_name, ticket_no);

EXPLAIN ANALYZE 
SELECT * FROM tickets 
WHERE passenger_name = 'VALENTINA AKIMOVA' AND ticket_no = '0005432000370';

EXPLAIN ANALYZE 
SELECT * FROM tickets WHERE passenger_name = 'VALENTINA AKIMOVA';
-- END

-- Задание 5
EXPLAIN ANALYZE
SELECT f.flight_id, f.flight_no, a.airport_name
FROM flights f
JOIN airports a ON f.departure_airport = a.airport_code
WHERE a.airport_name = 'Домодедово';

CREATE INDEX idx_airports_name ON airports (airport_name);

EXPLAIN ANALYZE
SELECT f.flight_id, f.flight_no, a.airport_name
FROM flights f
JOIN airports a ON f.departure_airport = a.airport_code
WHERE a.airport_name = 'Домодедово';

CREATE INDEX idx_flights_departure ON flights (departure_airport);

EXPLAIN ANALYZE
SELECT f.flight_id, f.flight_no, a.airport_name
FROM flights f
JOIN airports a ON f.departure_airport = a.airport_code
WHERE a.airport_name = 'Домодедово';
-- END
