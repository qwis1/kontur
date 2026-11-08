"""Подключение к SQLite и создание схемы базы данных."""

import os
import sqlite3
from contextlib import contextmanager

CREATE_REQUESTS_TABLE = """
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Новая',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""


def get_connection(db_path):
    """Создаёт и возвращает подключение к базе данных.

    :param db_path: путь к файлу SQLite;
    :return: объект sqlite3.Connection с доступом к строкам по имени поля.
    """
    if not db_path:
        raise ValueError("Не указан путь к базе данных.")

    directory = os.path.dirname(os.path.abspath(db_path))
    if directory:
        os.makedirs(directory, exist_ok=True)

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def database_connection(db_path):
    """Открывает подключение и гарантированно закрывает его после работы.

    :param db_path: путь к файлу SQLite;
    :yield: открытое подключение sqlite3.Connection.
    """
    connection = get_connection(db_path)
    try:
        yield connection
    finally:
        connection.close()


def init_db(db_path):
    """Создаёт файл базы данных и таблицу requests при первом запуске.

    :param db_path: путь к файлу SQLite.
    """
    with database_connection(db_path) as connection:
        connection.execute(CREATE_REQUESTS_TABLE)
        connection.commit()
