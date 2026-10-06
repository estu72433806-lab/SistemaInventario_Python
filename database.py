"""Acceso a MySQL para el sistema de inventario de escritorio."""

from contextlib import contextmanager
import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",  # <-- Cambia esto si tu MySQL Server tiene contraseña.
    "database": "inventario_computadoras",
    "autocommit": False,
}


@contextmanager
def get_connection():
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        yield conn
    finally:
        if conn is not None and conn.is_connected():
            conn.close()


def test_connection():
    try:
        with get_connection() as conn:
            return conn.is_connected(), "Conexión a MySQL correcta."
    except Error as exc:
        return False, str(exc)


def fetch_one(sql, params=()):
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        row = cur.fetchone()
        cur.close()
        return row


def fetch_all(sql, params=()):
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        return rows


def execute(sql, params=()):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        last_id = cur.lastrowid
        cur.close()
        return last_id


def execute_many(sql, rows):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.executemany(sql, rows)
        conn.commit()
        cur.close()


def execute_transaction(statements):
    """statements = [(sql, params), ...]. Hace COMMIT o ROLLBACK."""
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            for sql, params in statements:
                cur.execute(sql, params)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
