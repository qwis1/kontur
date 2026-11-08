"""Тесты модели Request."""

import pytest

from models.request import (
    ALLOWED_PRIORITIES,
    ALLOWED_STATUSES,
    Request,
    ValidationError,
)


def build_request(**overrides):
    """Создаёт корректную заявку с возможностью заменить отдельные поля."""
    data = {
        "title": "Настроить рабочее место",
        "description": "Требуется установить офисный пакет и настроить почту.",
        "category": "Программное обеспечение",
        "priority": "Средний",
        "status": "Новая",
    }
    data.update(overrides)
    return Request(**data)


def test_valid_request_passes_validation():
    """Корректная заявка не вызывает ошибок валидации."""
    request = build_request()

    request.validate()

    assert request.title == "Настроить рабочее место"
    assert request.priority in ALLOWED_PRIORITIES
    assert request.status in ALLOWED_STATUSES


def test_empty_title_raises_validation_error():
    """Пустое название заявки недопустимо."""
    request = build_request(title="   ")

    with pytest.raises(ValidationError) as error:
        request.validate()

    assert "Название заявки не может быть пустым" in str(error.value)


def test_missing_category_raises_validation_error():
    """Заявка без категории недопустима."""
    request = build_request(category="")

    with pytest.raises(ValidationError) as error:
        request.validate()

    assert "категорию" in str(error.value)


def test_invalid_priority_raises_validation_error():
    """Приоритет вне допустимого списка отклоняется."""
    request = build_request(priority="Критический")

    with pytest.raises(ValidationError) as error:
        request.validate()

    assert "Недопустимый приоритет" in str(error.value)


def test_invalid_status_raises_validation_error():
    """Статус вне допустимого списка отклоняется."""
    request = build_request(status="Отложена")

    with pytest.raises(ValidationError) as error:
        request.validate()

    assert "Недопустимый статус" in str(error.value)


def test_to_dict_returns_all_fields():
    """Метод to_dict возвращает полный набор полей заявки."""
    request = Request(
        request_id=7,
        title="Обновить антивирус",
        description="Обновить базы на компьютерах отдела продаж.",
        category="Программное обеспечение",
        priority="Низкий",
        status="В работе",
        created_at="2026-11-01 09:30:00",
        updated_at="2026-11-02 10:15:00",
    )

    data = request.to_dict()

    assert data == {
        "id": 7,
        "title": "Обновить антивирус",
        "description": "Обновить базы на компьютерах отдела продаж.",
        "category": "Программное обеспечение",
        "priority": "Низкий",
        "status": "В работе",
        "created_at": "2026-11-01 09:30:00",
        "updated_at": "2026-11-02 10:15:00",
    }


def test_from_row_creates_request():
    """Модель корректно создаётся из строки базы данных."""
    row = {
        "id": 3,
        "title": "Восстановить доступ",
        "description": "Пользователь забыл пароль.",
        "category": "Доступы и учётные записи",
        "priority": "Средний",
        "status": "Выполнена",
        "created_at": "2026-10-20 11:00:00",
        "updated_at": "2026-10-20 12:00:00",
    }

    request = Request.from_row(row)

    assert request.id == 3
    assert request.title == "Восстановить доступ"
    assert request.status == "Выполнена"
