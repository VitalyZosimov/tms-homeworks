-- Задача 1: Вывести аэропорты, из которых выполняется менее 50 рейсов
SELECT airport_name, COUNT(*) AS flight_count
FROM airports a
JOIN flights f ON a.airport_code = f.departure_airport
GROUP BY airport_name
HAVING COUNT(*) < 50
ORDER BY flight_count DESC;

-- Задача 2: Вывести среднюю стоимость билетов для каждого маршрута (город вылета - город прилёта)
select a1.city as dearture_city , a2.city as arrival_city , ROUND(AVG(tf.amount),2)
from flights f
join ticket_flights tf 
on f.flight_id = tf.flight_id
join airports a1
on a1.airport_code = f.departure_airport 
join airports a2
on a2.airport_code = f.arrival_airport
group by a1.city, a2.city

-- Задача 3: Вывести топ-5 самых загруженный маршрутов (по количеству проданных билетов)
select departure_airport, arrival_airport, count(*) as ticket_count
from ticket_flights tf 
join flights f 
on f.flight_id = tf.flight_id
group by departure_airport, arrival_airport
order by ticket_count desc
limit 5

-- Задача 4: Найти пары рейсов, вылетающих из одного аэропорта в течении 1 часа
select f1.departure_airport as first_flight_departure_airport, f1.arrival_airport as first_flight_arrival_airport, f1.scheduled_departure as first_flight_schedule_departure,
		f2.departure_airport as second_flight_departure_airport, f2.arrival_airport as second_flight_arrival_airport, f2.scheduled_departure as second_flight_schedule_departure
from flights f1
join flights f2
on f1.departure_airport  = f2.departure_airport and f1.flight_id < f2.flight_id
where ABS(EXTRACT(EPOCH FROM (f1.scheduled_departure - f2.scheduled_departure))) <= 3600

-- Задача 5:Проанализировать данные о продажах билетов, чтобы получить статистику в разных разрезах
SELECT
    tf.fare_conditions,
    EXTRACT(MONTH FROM f.scheduled_departure)  AS departure_month,
    f.departure_airport,
    COUNT(tf.ticket_no)                        AS ticket_count,
    ROUND(SUM(tf.amount), 2)                   AS total_revenue,
    ROUND(AVG(tf.amount), 2)                   AS avg_price
FROM ticket_flights tf
JOIN flights f ON f.flight_id = tf.flight_id
GROUP BY GROUPING SETS (
    (tf.fare_conditions),                          -- по классу
    (departure_month),                             -- по месяцу
    (f.departure_airport),                         -- по аэропорту
    (tf.fare_conditions, departure_month),         -- класс + месяц
    (tf.fare_conditions, f.departure_airport),     -- класс + аэропорт
    (departure_month,    f.departure_airport),     -- месяц + аэропорт
    ()                                             -- общий итог
)
ORDER BY
    tf.fare_conditions,
    departure_month,
    f.departure_airport
    
    -- Задача 6: Найти рейсы, задержа которых превышает среднюю задержку по всем рейсам
    with flight_delays as (
    select flight_id, flight_no, departure_airport, arrival_airport,  EXTRACT(EPOCH from (actual_departure - scheduled_departure)) / 60 as delay_minutes_departure, EXTRACT(EPOCH from (actual_arrival - scheduled_arrival )) / 60 as delay_minutes_arrival
    from flights f
    where actual_departure > scheduled_departure or actual_arrival > scheduled_arrival
    ),
	
    avg_delays as (
	select avg(delay_minutes_departure) as avg_delay_minutes_departure,
	avg(delay_minutes_arrival) as avg_delay_minutes_arrival
	from flight_delays
	)
	
	select *
	from flight_delays fd
	cross join avg_delays ad
	where delay_minutes_departure > avg_delay_minutes_departure or delay_minutes_arrival > avg_delay_minutes_arrival
	
