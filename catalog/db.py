import sqlite3
import json
import os

DB_NAME = "catalog.db"
DB_FILE = "db.json"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS catalog (
            id TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            price TEXT,
            photo TEXT
        )
    """)
    conn.commit()
    conn.close()


def add_item(item):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO catalog (id, title, description, price, photo)
        VALUES (?, ?, ?, ?, ?)
    """, (item["id"], item["title"], item["description"], item["price"], item["photo"]))
    conn.commit()
    conn.close()


def get_all_items():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, title, description, price, photo FROM catalog")
    rows = c.fetchall()
    conn.close()
    return [dict(zip(["id", "title", "description", "price", "photo"], row)) for row in rows]


def delete_item(item_id: str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM catalog WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()


def update_item(updated_item: dict):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        UPDATE catalog
        SET title = ?, description = ?, price = ?, photo = ?
        WHERE id = ?
    """, (updated_item["title"], updated_item["description"], updated_item["price"], updated_item["photo"], updated_item["id"]))
    conn.commit()
    conn.close()


def update_item_field(item_id: str, field: str, value: str):
    if field not in ("title", "description", "price", "photo"):
        raise ValueError("Недопустимое поле")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(f"UPDATE catalog SET {field} = ? WHERE id = ?", (value, item_id))
    conn.commit()
    conn.close()



