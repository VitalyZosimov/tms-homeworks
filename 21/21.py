import psycopg2
from psycopg2 import sql
import csv

DB_CONFIGURATION = {
    'host' : 'localhost',
    'port' : '5432',
    'database' : 'demo',
    'user' : 'postgres',
    'password' : 'password'
}

def get_connection():
    return psycopg2.connect(**DB_CONFIGURATION)

def export_flight_schedule(deparute_airport,arrival_airport):
    query = """select a2.city as departure_airport,a3.city as arrival_airport,f.flight_no, f.scheduled_departure, f.scheduled_arrival, a.model, ROUND(AVG(tf.amount),2)
        from bookings.flights f
        join bookings.aircrafts a
        on f.aircraft_code = a.aircraft_code
        join bookings.ticket_flights tf
        on f.flight_id = tf.flight_id
        join bookings.airports a2
        on f.departure_airport = a2.airport_code
        join bookings.airports a3
        on f.arrival_airport = a3.airport_code
        where a2.city = %s and a3.city = %s
        group by a2.city,a3.city,f.flight_no, f.scheduled_departure, f.scheduled_arrival, a.model"""
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query,(deparute_airport, arrival_airport))
                flights = cursor.fetchall()
                columns_name = [desc[0] for desc in cursor.description]

                with open("21/export_file.csv","w",encoding="utf-8", newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(columns_name)

                    writer.writerows(flights)
    except Exception as e:
        print(f"Ошибка функции: {e}")



departure_airport = input("Введите город отправления: ")
arrival_airport = input("Введите город отправления: ")

export_flight_schedule(departure_airport, arrival_airport)
