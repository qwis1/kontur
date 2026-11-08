"""Бизнес-логика работы с заявками."""

from database.request_repository import RequestRepository
from models.request import ALLOWED_STATUSES, Request, ValidationError


class RequestService:
    """Сервис заявок: валидация данных и вызовы слоя доступа к данным.

    Класс не зависит от Flask и может использоваться отдельно в тестах.
    """

    def __init__(self, database_path):
        """Создаёт сервис для указанной базы данных.

        :param database_path: путь к файлу SQLite.
        """
        self.repository = RequestRepository(database_path)

    def get_all_requests(self, status=None, category=None):
        """Возвращает заявки с необязательными фильтрами.

        :param status: статус для фильтрации;
        :param category: категория для фильтрации;
        :return: список объектов Request;
        :raises ValidationError: если передан недопустимый статус.
        """
        clean_status = (status or "").strip() or None
        clean_category = (category or "").strip() or None

        if clean_status and clean_status not in ALLOWED_STATUSES:
            raise ValidationError(
                "Недопустимый статус для фильтрации. "
                "Допустимые значения: Новая, В работе, Выполнена, Закрыта."
            )

        return self.repository.get_all(
            status=clean_status,
            category=clean_category,
        )

    def get_request_by_id(self, request_id):
        """Возвращает заявку по ID или None, если её нет."""
        return self.repository.get_by_id(request_id)

    def create_request(self, data):
        """Создаёт новую заявку после проверки данных.

        :param data: словарь с полями заявки;
        :return: сохранённый объект Request;
        :raises ValidationError: если данные некорректны.
        """
        if not isinstance(data, dict):
            raise ValidationError("Данные заявки должны быть объектом JSON.")

        request = Request(
            title=data.get("title"),
            description=data.get("description", ""),
            category=data.get("category"),
            priority=data.get("priority", "Средний"),
            status=data.get("status", "Новая"),
        )
        request.validate()
        return self.repository.create(request)

    def update_request(self, request_id, data):
        """Обновляет данные заявки.

        Статус через этот метод не изменяется — для него есть update_status.
        Не переданные поля сохраняют текущие значения.

        :param request_id: идентификатор заявки;
        :param data: словарь с новыми данными;
        :return: обновлённая заявка или None, если заявка не найдена;
        :raises ValidationError: если данные некорректны.
        """
        existing = self.repository.get_by_id(request_id)
        if existing is None:
            return None

        if not isinstance(data, dict):
            raise ValidationError("Данные заявки должны быть объектом JSON.")

        request = Request(
            request_id=existing.id,
            title=data.get("title", existing.title),
            description=data.get("description", existing.description),
            category=data.get("category", existing.category),
            priority=data.get("priority", existing.priority),
            status=existing.status,
            created_at=existing.created_at,
        )
        request.validate()

        return self.repository.update(
            request_id=request_id,
            title=request.title,
            description=request.description,
            category=request.category,
            priority=request.priority,
            status=request.status,
        )

    def update_status(self, request_id, status):
        """Изменяет статус заявки после проверки допустимых значений.

        :param request_id: идентификатор заявки;
        :param status: новый статус;
        :return: обновлённая заявка или None, если заявка не найдена;
        :raises ValidationError: если статус недопустим.
        """
        existing = self.repository.get_by_id(request_id)
        if existing is None:
            return None

        if isinstance(status, str):
            clean_status = status.strip()
        else:
            clean_status = ""
        if clean_status not in ALLOWED_STATUSES:
            raise ValidationError(
                "Недопустимый статус. "
                "Допустимые значения: Новая, В работе, Выполнена, Закрыта."
            )

        return self.repository.update_status(request_id, clean_status)

    def delete_request(self, request_id):
        """Удаляет заявку по идентификатору.

        :return: True, если заявка удалена, иначе False.
        """
        return self.repository.delete(request_id)
