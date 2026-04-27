    -- Задача 1: Найти рейсы, задержа которых превышает среднюю задержку по всем рейсам
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
	
	-- Задача 2: Создать VIEW для статистики по аэропортам
	create or replace view airport_statistics as
	select airport_code, city, count(f.flight_id) as flights_count
								,count(distinct f.arrival_airport)
								,ROUND(AVG(EXTRACT(EPOCH from (actual_departure - scheduled_departure)) / 60),2) as delay_minutes_departure,
								ROUND(AVG(EXTRACT(EPOCH from (actual_arrival - scheduled_arrival )) / 60),2) as delay_minutes_arrival
	from airports a
	left join flights f
	on a.airport_code = f.departure_airport
	group by airport_code, city
	
	-- Задача 3: Создать функцию, которая по коду аэропорта выводит его название
	CREATE OR REPLACE FUNCTION get_airport_info(p_airport_code TEXT)
RETURNS TEXT AS
$$
DECLARE
    v_airport_name TEXT;
BEGIN
    SELECT airport_name
    INTO v_airport_name
    FROM airports
    WHERE airport_code = p_airport_code;

    IF v_airport_name IS NULL THEN
        RETURN 'Аэропорт не найден';
    END IF;

    RETURN v_airport_name;
END;
$$
LANGUAGE plpgsql;
