"""REST API для работы с заявками."""

from flask import Blueprint, current_app, jsonify, request

from models.request import ValidationError

request_bp = Blueprint("requests", __name__, url_prefix="/api/requests")


def get_service():
    """Возвращает сервис заявок, созданный при запуске приложения."""
    return current_app.extensions["request_service"]


def validation_error_response(error):
    """Формирует JSON-ответ с сообщениями валидации."""
    return jsonify(
        {
            "error": error.errors[0],
            "details": error.errors,
        }
    ), 400


def not_found_response(request_id):
    """Формирует JSON-ответ для несуществующей заявки."""
    return jsonify({"error": f"Заявка с ID {request_id} не найдена."}), 404


@request_bp.route("", methods=["GET"])
def get_requests():
    """Возвращает все заявки с фильтрацией по статусу и категории."""
    status = request.args.get("status")
    category = request.args.get("category")

    try:
        requests = get_service().get_all_requests(
            status=status,
            category=category,
        )
    except ValidationError as error:
        return validation_error_response(error)

    return jsonify([item.to_dict() for item in requests]), 200


@request_bp.route("/<int:request_id>", methods=["GET"])
def get_request(request_id):
    """Возвращает одну заявку по идентификатору."""
    found_request = get_service().get_request_by_id(request_id)
    if found_request is None:
        return not_found_response(request_id)

    return jsonify(found_request.to_dict()), 200


@request_bp.route("", methods=["POST"])
def create_request():
    """Создаёт заявку из JSON-тела запроса."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(
            {
                "error": "Некорректный JSON. "
                "Ожидается объект с данными заявки."
            }
        ), 400

    try:
        created_request = get_service().create_request(data)
    except ValidationError as error:
        return validation_error_response(error)

    return jsonify(created_request.to_dict()), 201


@request_bp.route("/<int:request_id>", methods=["PUT"])
def update_request(request_id):
    """Обновляет название, описание, категорию и приоритет заявки."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(
            {
                "error": "Некорректный JSON. "
                "Ожидается объект с данными заявки."
            }
        ), 400

    try:
        updated_request = get_service().update_request(request_id, data)
    except ValidationError as error:
        return validation_error_response(error)

    if updated_request is None:
        return not_found_response(request_id)

    return jsonify(updated_request.to_dict()), 200


@request_bp.route("/<int:request_id>/status", methods=["PATCH"])
def update_request_status(request_id):
    """Изменяет статус заявки."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(
            {
                "error": "Некорректный JSON. "
                "Ожидается объект с полем status."
            }
        ), 400

    if "status" not in data:
        return jsonify({"error": "Поле status обязательно."}), 400

    try:
        updated_request = get_service().update_status(
            request_id,
            data.get("status"),
        )
    except ValidationError as error:
        return validation_error_response(error)

    if updated_request is None:
        return not_found_response(request_id)

    return jsonify(updated_request.to_dict()), 200


@request_bp.route("/<int:request_id>", methods=["DELETE"])
def delete_request(request_id):
    """Удаляет заявку по идентификатору."""
    deleted = get_service().delete_request(request_id)
    if not deleted:
        return not_found_response(request_id)

    return jsonify(
        {
            "message": "Заявка успешно удалена.",
            "id": request_id,
        }
    ), 200
