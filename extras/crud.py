"""
Kyros CRUD Demonstration
Demonstrates Create, Read, Update, and Delete operations
using a simple SQL database.
"""

import sqlite3

DB_NAME = "crud_demo.db"


def create_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS apis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            status TEXT DEFAULT 'active'
        )
    """)

    conn.commit()
    conn.close()


def create_api(name, endpoint):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO apis (name, endpoint) VALUES (?, ?)",
        (name, endpoint)
    )

    conn.commit()
    conn.close()


def read_apis():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM apis")
    records = cursor.fetchall()

    conn.close()
    return records


def update_api(api_id, status):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE apis SET status = ? WHERE id = ?",
        (status, api_id)
    )

    conn.commit()
    conn.close()


def delete_api(api_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM apis WHERE id = ?",
        (api_id,)
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_table()

    create_api("Payments API", "/payments")
    print("Records:", read_apis())

    update_api(1, "degraded")
    print("After update:", read_apis())

    delete_api(1)
    print("After delete:", read_apis())