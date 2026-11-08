"""Интеграционные тесты REST API."""

API_URL = "/api/requests"


def create_request(client, **overrides):
    """Отправляет POST-запрос на создание заявки и возвращает ответ."""
    payload = {
        "title": "Не работает принтер",
        "description": "Принтер не печатает документы.",
        "category": "Оборудование",
        "priority": "Высокий",
    }
    payload.update(overrides)
    return client.post(API_URL, json=payload)


def test_get_requests_returns_empty_list(client):
    """В пустой базе список заявок — пустой JSON-массив."""
    response = client.get(API_URL)

    assert response.status_code == 200
    assert response.get_json() == []
    assert response.is_json


def test_create_request_success(client):
    """Корректная заявка создаётся со статусом «Новая» и HTTP 201."""
    response = create_request(client)

    assert response.status_code == 201
    data = response.get_json()
    assert data["id"] > 0
    assert data["title"] == "Не работает принтер"
    assert data["category"] == "Оборудование"
    assert data["priority"] == "Высокий"
    assert data["status"] == "Новая"
    assert data["created_at"]
    assert data["updated_at"]


def test_create_request_without_title(client):
    """Заявка с пустым названием отклоняется с HTTP 400."""
    response = create_request(client, title="   ")

    assert response.status_code == 400
    data = response.get_json()
    assert "Название заявки не может быть пустым" in data["error"]
    assert data["details"]


def test_create_request_without_category(client):
    """Заявка без категории отклоняется с HTTP 400."""
    response = create_request(client, category="")

    assert response.status_code == 400
    data = response.get_json()
    assert "категорию" in data["error"]


def test_create_request_with_invalid_priority(client):
    """Заявка с недопустимым приоритетом отклоняется."""
    response = create_request(client, priority="Критический")

    assert response.status_code == 400
    assert "Недопустимый приоритет" in response.get_json()["error"]


def test_create_request_with_invalid_json(client):
    """Некорректный JSON возвращает понятную ошибку."""
    response = client.post(
        API_URL,
        data='{"title": "Некорректный JSON"',
        content_type="application/json",
    )

    assert response.status_code == 400
    assert "Некорректный JSON" in response.get_json()["error"]


def test_get_request_by_id(client, sample_request):
    """Существующая заявка возвращается по идентификатору."""
    response = client.get(f"{API_URL}/{sample_request['id']}")

    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == sample_request["id"]
    assert data["title"] == "Не работает принтер"


def test_get_missing_request_returns_404(client):
    """Запрос несуществующей заявки возвращает HTTP 404 и JSON."""
    response = client.get(f"{API_URL}/9999")

    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "Заявка с ID 9999 не найдена."


def test_update_request_status(client, sample_request):
    """Статус заявки изменяется через PATCH."""
    response = client.patch(
        f"{API_URL}/{sample_request['id']}/status",
        json={"status": "В работе"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "В работе"

    check_response = client.get(f"{API_URL}/{sample_request['id']}")
    assert check_response.get_json()["status"] == "В работе"


def test_update_request_with_invalid_status(client, sample_request):
    """Недопустимый статус отклоняется с HTTP 400."""
    response = client.patch(
        f"{API_URL}/{sample_request['id']}/status",
        json={"status": "Отложена"},
    )

    assert response.status_code == 400
    assert "Недопустимый статус" in response.get_json()["error"]


def test_update_request_status_without_field(client, sample_request):
    """PATCH без поля status возвращает HTTP 400."""
    response = client.patch(
        f"{API_URL}/{sample_request['id']}/status",
        json={"comment": "Без статуса"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Поле status обязательно."


def test_update_request_data(client, sample_request):
    """PUT изменяет название, описание, категорию и приоритет."""
    response = client.put(
        f"{API_URL}/{sample_request['id']}",
        json={
            "title": "Заменить картридж",
            "description": "Требуется новый картридж для принтера.",
            "category": "Оборудование",
            "priority": "Средний",
        },
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["title"] == "Заменить картридж"
    assert data["description"] == "Требуется новый картридж для принтера."
    assert data["priority"] == "Средний"
    assert data["status"] == "Новая"


def test_delete_request(client, sample_request):
    """Удаление существующей заявки возвращает сообщение об успехе."""
    response = client.delete(f"{API_URL}/{sample_request['id']}")

    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == sample_request["id"]
    assert data["message"] == "Заявка успешно удалена."

    check_response = client.get(f"{API_URL}/{sample_request['id']}")
    assert check_response.status_code == 404


def test_delete_missing_request_returns_404(client):
    """Повторное удаление несуществующей заявки возвращает HTTP 404."""
    response = client.delete(f"{API_URL}/9999")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Заявка с ID 9999 не найдена."


def test_filter_requests_by_status(client):
    """Фильтр по статусу возвращает только подходящие заявки."""
    first = create_request(client, title="Первая заявка").get_json()
    second = create_request(client, title="Вторая заявка").get_json()

    client.patch(
        f"{API_URL}/{second['id']}/status",
        json={"status": "В работе"},
    )

    response = client.get(API_URL, query_string={"status": "В работе"})

    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["id"] == second["id"]
    assert data[0]["title"] == "Вторая заявка"
    assert data[0]["id"] != first["id"]


def test_filter_requests_by_category(client):
    """Фильтр по категории возвращает только подходящие заявки."""
    create_request(client, title="Принтер", category="Оборудование")
    create_request(client, title="Почта", category="Программное обеспечение")

    response = client.get(
        API_URL,
        query_string={"category": "Программное обеспечение"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["title"] == "Почта"
    assert data[0]["category"] == "Программное обеспечение"


def test_filter_by_invalid_status_returns_400(client):
    """Недопустимый статус в фильтре приводит к HTTP 400."""
    response = client.get(API_URL, query_string={"status": "Отложена"})

    assert response.status_code == 400
    assert "Недопустимый статус для фильтрации" in response.get_json()["error"]


def test_unsupported_method_returns_json_error(client):
    """Неподдерживаемый HTTP-метод возвращает JSON-ошибку."""
    response = client.patch(API_URL, json={})

    assert response.status_code == 405
    assert response.is_json
    assert "не поддерживается" in response.get_json()["error"]
