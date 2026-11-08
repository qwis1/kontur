"""Конфигурация Flask-приложения «Контур»."""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_DATABASE_PATH = os.path.join(BASE_DIR, "instance", "kontur.db")


class Config:
    """Базовые настройки приложения.

    Значения можно переопределить переменными окружения, не изменяя код.
    """

    DEBUG = False

    # Путь к файлу SQLite. В тестах это значение заменяется на временный файл.
    DATABASE_PATH = os.environ.get(
        "KONTUR_DATABASE_PATH",
        DEFAULT_DATABASE_PATH,
    )

    SECRET_KEY = os.environ.get("KONTUR_SECRET_KEY", "kontur-study-project")
