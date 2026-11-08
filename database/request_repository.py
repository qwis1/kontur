"""Слой доступа к данным для таблицы requests."""

from datetime import datetime

from database.database import database_connection
from models.request import Request

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def current_timestamp():
    """Возвращает текущую дату и время в формате, удобном для SQLite."""
    return datetime.now().strftime(DATE_FORMAT)


class RequestRepository:
    """Выполняет CRUD-операции с заявками.

    Все SQL-запросы параметризованы, поэтому данные пользователя
    не попадают в текст запроса напрямую.
    """

    def __init__(self, database_path):
        """Сохраняет путь к базе данных.

        :param database_path: путь к файлу SQLite.
        """
        self.database_path = database_path

    def get_all(self, status=None, category=None):
        """Возвращает список заявок с необязательной фильтрацией.

        :param status: статус заявки или None;
        :param category: категория заявки или None;
        :return: список объектов Request, сначала новые заявки.
        """
        query = "SELECT * FROM requests"
        conditions = []
        parameters = []

        if status:
            conditions.append("status = ?")
            parameters.append(status)
        if category:
            conditions.append("category = ?")
            parameters.append(category)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY id DESC"

        with database_connection(self.database_path) as connection:
            rows = connection.execute(query, parameters).fetchall()

        return [Request.from_row(row) for row in rows]

    def get_by_id(self, request_id):
        """Находит заявку по идентификатору.

        :param request_id: числовой идентификатор заявки;
        :return: объект Request или None.
        """
        with database_connection(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM requests WHERE id = ?",
                (request_id,),
            ).fetchone()

        if row is None:
            return None
        return Request.from_row(row)

    def create(self, request):
        """Сохраняет новую заявку в базе данных.

        :param request: проверенный объект Request;
        :return: сохранённая заявка с заполненными id и датами.
        """
        timestamp = current_timestamp()

        with database_connection(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO requests
                    (title, description, category, priority, status,
                     created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request.title,
                    request.description,
                    request.category,
                    request.priority,
                    request.status,
                    timestamp,
                    timestamp,
                ),
            )
            connection.commit()
            request_id = cursor.lastrowid

        return self.get_by_id(request_id)

    def update(
        self,
        request_id,
        title,
        description,
        category,
        priority,
        status,
    ):
        """Обновляет основные данные существующей заявки.

        :return: обновлённая заявка или None, если заявка не найдена.
        """
        with database_connection(self.database_path) as connection:
            cursor = connection.execute(
                """
                UPDATE requests
                SET title = ?, description = ?, category = ?,
                    priority = ?, status = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    title,
                    description,
                    category,
                    priority,
                    status,
                    current_timestamp(),
                    request_id,
                ),
            )
            connection.commit()
            updated_rows = cursor.rowcount

        if updated_rows == 0:
            return None
        return self.get_by_id(request_id)

    def update_status(self, request_id, status):
        """Меняет только статус заявки.

        :return: обновлённая заявка или None, если заявка не найдена.
        """
        with database_connection(self.database_path) as connection:
            cursor = connection.execute(
                """
                UPDATE requests
                SET status = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, current_timestamp(), request_id),
            )
            connection.commit()
            updated_rows = cursor.rowcount

        if updated_rows == 0:
            return None
        return self.get_by_id(request_id)

    def delete(self, request_id):
        """Удаляет заявку по идентификатору.

        :return: True, если заявка удалена, иначе False.
        """
        with database_connection(self.database_path) as connection:
            cursor = connection.execute(
                "DELETE FROM requests WHERE id = ?",
                (request_id,),
            )
            connection.commit()
            deleted_rows = cursor.rowcount

        return deleted_rows > 0
