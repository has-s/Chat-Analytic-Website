from flask import Flask
from routes import main
from config import Config

def create_app():
    """Создает и настраивает приложение Flask."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Регистрируем маршруты
    app.register_blueprint(main)

    return app

# Создаем приложение
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)