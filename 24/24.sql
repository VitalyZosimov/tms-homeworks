CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_flights_status_date 
ON flights (status, actual_departure) 
WHERE status = 'Arrived';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_boarding_passes_flight_id 
ON boarding_passes (flight_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_seats_aircraft_code 
ON seats (aircraft_code);


EXPLAIN ANALYZE
WITH flight_stats AS (
    SELECT 
        f.flight_id,
        f.flight_no,
        f.aircraft_code,
        COUNT(DISTINCT bp.seat_no) AS occupied_seats,
        (
            SELECT COUNT(*) 
            FROM seats s 
            WHERE s.aircraft_code = f.aircraft_code
        ) AS total_seats
    FROM flights f
    LEFT JOIN boarding_passes bp ON f.flight_id = bp.flight_id
    WHERE f.status = 'Arrived'
        AND f.actual_departure >= '2016-09-01'
        AND f.actual_departure < '2016-10-01'
    GROUP BY f.flight_id, f.flight_no, f.aircraft_code
)
SELECT 
    flight_id,
    flight_no,
    aircraft_code,
    occupied_seats,
    total_seats,
    ROUND((occupied_seats::NUMERIC / total_seats) * 100, 2) AS load_percentage
FROM flight_stats
ORDER BY load_percentage DESC;



-- Более оптимизированный вариант без вложенностей =)
EXPLAIN (ANALYZE, BUFFERS, TIMING)
WITH 

aircraft_capacity AS (
    SELECT 
        aircraft_code,
        COUNT(*) AS total_seats
    FROM seats
    GROUP BY aircraft_code  
),

filtered_flights AS (
    SELECT 
        f.flight_id,
        f.flight_no,
        f.aircraft_code,
        COUNT(bp.seat_no) AS occupied_seats  
    FROM flights f
    LEFT JOIN boarding_passes bp ON f.flight_id = bp.flight_id
    WHERE f.status = 'Arrived'
        AND f.actual_departure >= '2016-09-01'
        AND f.actual_departure < '2016-10-01'
    GROUP BY f.flight_id, f.flight_no, f.aircraft_code  
)

SELECT 
    ff.flight_id,
    ff.flight_no,
    ff.aircraft_code,
    ff.occupied_seats,
    ac.total_seats,
    ROUND((ff.occupied_seats::NUMERIC / ac.total_seats) * 100, 2) AS load_percentage
FROM filtered_flights ff
JOIN aircraft_capacity ac ON ff.aircraft_code = ac.aircraft_code
ORDER BY load_percentage DESC;
