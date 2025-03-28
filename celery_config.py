from celery import Celery
from config import Config

def make_celery():
    """Функция для создания Celery."""
    celery = Celery(
        'dip',  # Название приложения
        backend=Config.CELERY_RESULT_BACKEND,
        broker=Config.CELERY_BROKER_URL
    )
    # Обновляем конфигурацию Celery
    celery.conf.update(
        accept_content=Config.CELERY_ACCEPT_CONTENT,
        task_serializer=Config.CELERY_TASK_SERIALIZER,
        result_serializer=Config.CELERY_RESULT_SERIALIZER
    )
    return celery