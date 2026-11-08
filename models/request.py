"""Модель заявки и правила её валидации."""

ALLOWED_PRIORITIES = ("Низкий", "Средний", "Высокий")
ALLOWED_STATUSES = ("Новая", "В работе", "Выполнена", "Закрыта")

MAX_TITLE_LENGTH = 120
MAX_DESCRIPTION_LENGTH = 2000
MAX_CATEGORY_LENGTH = 80


class ValidationError(ValueError):
    """Ошибка валидации данных заявки.

    Хранит список сообщений, чтобы API могло вернуть их все сразу.
    """

    def __init__(self, errors):
        if isinstance(errors, str):
            errors = [errors]
        self.errors = list(errors)
        super().__init__(" ".join(self.errors))


class Request:
    """Внутренняя заявка организации.

    Поля объекта соответствуют колонкам таблицы requests.
    """

    def __init__(
        self,
        title,
        description="",
        category="",
        priority="Средний",
        status="Новая",
        request_id=None,
        created_at=None,
        updated_at=None,
    ):
        """Создаёт объект заявки без сохранения в базе данных.

        Строковые значения очищаются от лишних пробелов по краям.
        """
        self.id = request_id
        self.title = self._clean_text(title)
        self.description = self._clean_text(description)
        self.category = self._clean_text(category)
        self.priority = self._clean_text(priority)
        self.status = self._clean_text(status)
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def _clean_text(value):
        """Приводит значение к строке и удаляет пробелы по краям."""
        if value is None:
            return ""
        return str(value).strip()

    def validate(self):
        """Проверяет обязательные поля и допустимые значения.

        :raises ValidationError: если найдена хотя бы одна ошибка.
        """
        errors = []

        if not self.title:
            errors.append("Название заявки не может быть пустым.")
        elif len(self.title) > MAX_TITLE_LENGTH:
            errors.append(
                "Название заявки не должно превышать "
                f"{MAX_TITLE_LENGTH} символов."
            )

        if not self.category:
            errors.append("Необходимо указать категорию заявки.")
        elif len(self.category) > MAX_CATEGORY_LENGTH:
            errors.append(
                "Категория не должна превышать "
                f"{MAX_CATEGORY_LENGTH} символов."
            )

        if self.priority not in ALLOWED_PRIORITIES:
            errors.append(
                "Недопустимый приоритет. "
                "Допустимые значения: Низкий, Средний, Высокий."
            )

        if self.status not in ALLOWED_STATUSES:
            errors.append(
                "Недопустимый статус. "
                "Допустимые значения: Новая, В работе, Выполнена, Закрыта."
            )

        if len(self.description) > MAX_DESCRIPTION_LENGTH:
            errors.append(
                "Описание не должно превышать "
                f"{MAX_DESCRIPTION_LENGTH} символов."
            )

        if errors:
            raise ValidationError(errors)

    def to_dict(self):
        """Преобразует заявку в словарь для JSON-ответа."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_row(cls, row):
        """Создаёт объект заявки из строки базы данных SQLite.

        :param row: строка sqlite3.Row или обычный словарь;
        :return: экземпляр Request.
        """
        data = dict(row)
        return cls(
            request_id=data["id"],
            title=data["title"],
            description=data["description"],
            category=data["category"],
            priority=data["priority"],
            status=data["status"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )

    def __repr__(self):
        """Возвращает отладочное представление заявки."""
        return (
            f"Request(id={self.id!r}, title={self.title!r}, "
            f"status={self.status!r})"
        )
