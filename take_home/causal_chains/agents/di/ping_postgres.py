import psycopg


def ping_postgres(database_url: str) -> bool:
    try:
        with psycopg.connect(database_url, connect_timeout=2) as connection:
            connection.execute("SELECT 1")
        return True
    except Exception:
        return False
