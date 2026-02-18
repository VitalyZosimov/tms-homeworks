-- Найти рейсы в бизнес-классе вылетающие из Москвы
SELECT DISTINCT 
       f.flight_id,
       f.flight_no,
       f.scheduled_departure,
       a.city,
       tf.fare_conditions
FROM flights f
JOIN airports a 
    ON f.departure_airport = a.airport_code
JOIN ticket_flights tf 
    ON f.flight_id = tf.flight_id
WHERE a.city = 'Москва'
  AND tf.fare_conditions = 'Business';


-- Найти самолеты, которые не учавствовали в полётах
SELECT *
FROM aircrafts a
LEFT JOIN flights f
       ON a.aircraft_code = f.aircraft_code
WHERE f.aircraft_code IS NULL;