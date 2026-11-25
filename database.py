
import os
import pyodbc
from dotenv import load_dotenv
from contextlib import contextmanager

load_dotenv()


def get_connection():
    connection_string = os.getenv("SQLSERVER_CONN_STR")

    if not connection_string:
        raise RuntimeError("Database connection string not found!")

    return pyodbc.connect(connection_string)


@contextmanager
def get_cursor(commit=False):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        yield cursor

        if commit:
            conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()
