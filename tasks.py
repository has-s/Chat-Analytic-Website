from celery import Celery
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from data_processors.stream_compose import collect_stream_data, save_stream_data
from data_processors.analytic_composer import analyze_stream_data

# Пример создания Celery приложения
app = Celery('tasks', broker='pyamqp://guest@localhost//')

# Загружаем конфигурацию (если нужно)
load_dotenv()
PROJECT_ROOT = os.getenv('PROJECT_ROOT')  # Для теста можно использовать /tmp
STORAGE_PATHS = [os.path.join(PROJECT_ROOT, 'stream_data'), os.path.join(PROJECT_ROOT, 'chats')]


# Функция для очистки старых файлов
def get_folder_size(path):
    """Возвращает размер папки в мегабайтах."""
    return sum(f.stat().st_size for f in Path(path).rglob("*") if f.is_file()) / (1024 * 1024)

def delete_old_streams(paths=None, max_age_days=30, max_folder_size_mb=5000, max_size_mb=500):
    """Удаляет файлы трансляций, если они старше max_age_days, больше max_size_mb или если папка превышает
    max_folder_size_mb."""
    if paths is None:
        paths = ['/tmp/stream_data', '/tmp/chats']

    now = time.time()
    max_age_seconds = max_age_days * 86400  # 30 дней в секундах
    deleted = 0

    for storage_path in paths:
        storage_dir = Path(storage_path)
        if not storage_dir.exists():
            continue

        # Удаляем файлы, которые слишком старые или большие
        files = list(storage_dir.iterdir())
        for file in files:
            if file.is_file():
                file_stat = file.stat()
                file_age = now - file_stat.st_atime  # Время последнего доступа
                file_size = file_stat.st_size / (1024 * 1024)  # В МБ

                # Удаляем файлы, которые слишком старые или большие
                if file_age > max_age_seconds or file_size > max_size_mb:
                    try:
                        os.remove(file)
                        deleted += 1
                        print(f"Удалён файл: {file}")
                    except Exception as e:
                        print(f"Не удалось удалить файл {file}: {e}")

        # Проверяем, не превышен ли размер папки
        while get_folder_size(storage_path) > max_folder_size_mb:
            oldest_file = min(storage_dir.iterdir(), key=lambda f: f.stat().st_mtime, default=None)
            if oldest_file and oldest_file.is_file():
                try:
                    os.remove(oldest_file)
                    deleted += 1
                    print(f"Удалён старый файл: {oldest_file}")
                except Exception as e:
                    print(f"Не удалось удалить файл {oldest_file}: {e}")

    return deleted


# Задача для сохранения данных о стриме
@app.task(bind=True)
def save_stream_task(self, vod_id):
    try:
        # Собираем данные о трансляции
        stream_data = collect_stream_data(vod_id)
        # Сохраняем данные в файл
        file_path = save_stream_data(vod_id, stream_data)
        if file_path:
            return {'status': 'success', 'file_path': file_path}
        else:
            return {'status': 'error', 'message': 'Ошибка при сохранении файла.'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@app.task(bind=True)
def run_analysis_task(self, vod_id, metrics, top_chatters_count=10, keywords="", top_pastes_count=10, emoticons_count=10):
    try:
        # Подготовка входных данных в нужной структуре
        input_data = {
            "received_data": {
                "vod_id": vod_id,
                "metrics": metrics,
                "top_chatters_count": top_chatters_count,
                "keywords": keywords,
                "top_pastes_count": top_pastes_count,
                "emoticons_count": emoticons_count,
            },
            "status": "success"
        }

        # Вызов основной аналитической функции
        analysis_result = analyze_stream_data(input_data)

        # Если внутри анализа что-то пошло не так — пробрасываем сообщение
        if isinstance(analysis_result, dict) and analysis_result.get("status") == "error":
            return {
                "status": "error",
                "message": analysis_result.get("message", "Неизвестная ошибка анализа")
            }

        # Вызов задачи очистки после успешного анализа
        cleanup_task.apply_async((STORAGE_PATHS,), kwargs={'max_age_days': 30, 'max_folder_size_mb': 5000, 'max_size_mb': 500})

        return {
            "status": "success",
            "received_data": input_data["received_data"],
            "analysis_result": analysis_result
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

# Задача для очистки старых файлов
@app.task(bind=True)
def cleanup_task(self, paths=None, max_age_days=60, max_folder_size_mb=10000, max_size_mb=100):
    try:
        # Выполнение очистки
        deleted_files_count = delete_old_streams(paths, max_age_days, max_folder_size_mb, max_size_mb)

        return {'status': 'success', 'deleted_files': deleted_files_count}

    except Exception as e:
        return {'status': 'error', 'message': str(e)}