import psycopg2
from psycopg2.extras import execute_values

DB_CONFIGURATION = {
    'host' : 'localhost',
    'port' : '5432',
    'database' : 'demo',
    'user' : 'postgres',
    'password' : 'password'
}

def get_connection():
    return psycopg2.connect(**DB_CONFIGURATION)

def update_flights_status(updates: list):
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                values = [(item["flight_id"], item["new_status"]) for item in updates]
                query = """
                UPDATE bookings.flights f
                SET status = v.new_status
                FROM (VALUES %s) AS v(id, new_status)
                WHERE f.flight_id = v.id
                RETURNING f.flight_id
                """
                execute_values(cursor, query, values)
    except Exception as e:
        print(f"ERROR: {e}")
    

    finally:
        connection.close()

update_flights_status(updates = [
    {"flight_id": 1233, "new_status": "Cancelled"},
    {"flight_id": 456, "new_status": "Cancelled"}
])
