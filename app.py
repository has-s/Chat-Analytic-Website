from flask import Flask
from config import Config
from celery import Celery
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

celery = Celery(__name__, broker=Config.CELERY_BROKER_URL, backend=Config.CELERY_RESULT_BACKEND)

# Инициализация лимитера вне функции, чтобы можно было использовать декораторы
limiter = Limiter(key_func=get_remote_address)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Инициализация Flask-Limiter с текущим приложением
    limiter.init_app(app)

    # Регистрация blueprint
    from routes import main
    app.register_blueprint(main)

    # Обновляем конфигурацию Celery
    celery.conf.update(app.config)

    return app