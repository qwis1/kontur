"""Точка входа Flask-приложения «Контур»."""

from flask import Flask, jsonify, render_template, request

from config import Config
from database.database import init_db
from routes.request_routes import request_bp
from services.request_service import RequestService


def create_app(test_config=None):
    """Создаёт и настраивает экземпляр Flask-приложения.

    Функция-фабрика позволяет создавать отдельные приложения
    с разными настройками, что удобно при автоматическом тестировании.

    :param test_config: словарь с настройками для тестов;
    :return: готовое Flask-приложение.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    # Русский текст в JSON остаётся читаемым, а не \u-последовательностями.
    app.json.ensure_ascii = False
    app.json.sort_keys = False

    # База данных создаётся автоматически при первом запуске.
    init_db(app.config["DATABASE_PATH"])

    # Сервис хранится в расширениях приложения и доступен маршрутам.
    app.extensions["request_service"] = RequestService(
        app.config["DATABASE_PATH"]
    )

    app.register_blueprint(request_bp)

    @app.route("/")
    def index():
        """Отображает главную страницу приложения."""
        return render_template("index.html")

    @app.errorhandler(404)
    def handle_not_found(error):
        """Возвращает JSON для неизвестных адресов API."""
        if request.path.startswith("/api/"):
            return jsonify({"error": "Маршрут API не найден."}), 404
        return "Страница не найдена.", 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Возвращает JSON при неподдерживаемом HTTP-методе."""
        if request.path.startswith("/api/"):
            message = "Метод запроса не поддерживается для этого маршрута."
            return jsonify({"error": message}), 405
        return "Метод не разрешён.", 405

    @app.errorhandler(500)
    def handle_internal_error(error):
        """Возвращает понятное сообщение при непредвиденной ошибке."""
        message = "Внутренняя ошибка сервера. Попробуйте позже."
        if request.path.startswith("/api/"):
            return jsonify({"error": message}), 500
        return message, 500

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(host="127.0.0.1", port=5000, debug=True)
