"""Общие pytest-фикстуры.

Каждый тест получает отдельное Flask-приложение и отдельный файл SQLite
во временной папке, поэтому основная база данных не изменяется.
"""

import pytest

from app import create_app


@pytest.fixture()
def app(tmp_path):
    """Создаёт тестовое Flask-приложение с временной базой данных."""
    database_path = tmp_path / "test_kontur.db"
    application = create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": str(database_path),
        }
    )
    yield application


@pytest.fixture()
def client(app):
    """Возвращает тестовый клиент Flask для HTTP-запросов."""
    return app.test_client()


@pytest.fixture()
def sample_request(client):
    """Создаёт одну заявку и возвращает её JSON-представление."""
    response = client.post(
        "/api/requests",
        json={
            "title": "Не работает принтер",
            "description": "Принтер не печатает документы из бухгалтерии.",
            "category": "Оборудование",
            "priority": "Высокий",
        },
    )
    assert response.status_code == 201
    return response.get_json()
