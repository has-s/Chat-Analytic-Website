from dotenv import load_dotenv
import os


def load_environment():
    """Загружает переменные окружения из файла .env локально или в Docker."""
    env_file = '.env.local' if os.environ.get('FLASK_ENV') == 'development' else '.env.docker'
    base_dir = os.path.abspath(os.path.dirname(__file__))
    env_path = os.path.join(base_dir, env_file)  # ищем файл на уровень выше (в корне проекта)

    load_dotenv(dotenv_path=env_path)

# Вызываем загрузку переменных окружения при запуске
load_environment()


class Config:
    """Конфигурация для Flask и Celery."""

    MAX_WORKERS = os.getenv("MAX_WORKERS")
    SECRET_KEY = os.getenv("SECRET_KEY")  # Взять секретный ключ из переменных окружения
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')  # Брокер сообщений Celery
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND')  # Бэкенд для хранения результатов
    CELERY_ACCEPT_CONTENT = ['json']  # Типы контента, которые Celery будет обрабатывать
    CELERY_TASK_SERIALIZER = 'json'  # Формат сериализации задач
    CELERY_RESULT_SERIALIZER = 'json'  # Формат сериализации результатов