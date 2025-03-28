from celery import Celery
from celery_config import make_celery
from config import Config

# Здесь создаём Celery, передавая Flask-приложение в make_celery
# Но не импортируем приложение напрямую из `app.py`, чтобы избежать циклических импортов.
celery = make_celery()

@celery.task
def take_stream_data(vod_id):
    """Задача для анализа данных по VOD ID."""
    # Логика анализа
    return f"Данные для VOD ID {vod_id} успешно проанализированы."