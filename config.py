import os

def get_project_root():
    # Получаем текущую директорию (где находится этот скрипт)
    current_path = os.path.abspath(__file__)

    # Поднимаемся по каталогам до тех пор, пока не найдем корень проекта
    while not os.path.exists(os.path.join(current_path, 'setup.py')) and not os.path.exists(os.path.join(current_path, '.env')):
        current_path = os.path.dirname(current_path)

    return current_path

# Глобальная переменная для корня проекта
PROJECT_ROOT = get_project_root()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")