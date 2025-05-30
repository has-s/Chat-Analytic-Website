from celery import Celery
import os
from dotenv import load_dotenv
from data_processors.stream_compose import collect_stream_data, save_stream_data
from data_processors.analytic_composer import analyze_stream_data
from data_processors.data_storage import delete_old_streams  # Импортируем функцию из нового модуля

# Пример создания Celery приложения
app = Celery('tasks', broker='pyamqp://guest@localhost//')

# Загружаем конфигурацию (если нужно)
# Загрузим .env.local.local для локальной разработки
if os.environ.get('FLASK_ENV') == 'development':
    load_dotenv('.env.local')
else:
    load_dotenv('.env.docker')

PROJECT_ROOT = os.getenv('PROJECT_ROOT')  # Для теста можно использовать /tmp
STORAGE_PATHS = [os.path.join(PROJECT_ROOT, 'stream_data'), os.path.join(PROJECT_ROOT, 'chats')]


# Задача для сохранения данных о стриме
@app.task(bind=True)
def save_stream_task(self, vod_id):
    try:
        # Собираем данные о трансляции
        stream_data = collect_stream_data(vod_id)

        if not stream_data:
            return {'status': 'error', 'message': 'Не удалось собрать данные для трансляции'}

        # Сохраняем данные в файл, используя vod_id в качестве имени
        file_path = save_stream_data(vod_id, stream_data)

        if file_path:
            # Возвращаем путь к файлу (или его имя)
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

@app.task(bind=True)
def cleanup_task(self, paths=None, max_age_days=60, max_folder_size_mb=10000, max_size_mb=100):
    try:
        # Выполнение очистки
        deleted_files_count = delete_old_streams(paths, max_age_days, max_folder_size_mb, max_size_mb)

        return {'status': 'success', 'deleted_files': deleted_files_count}

    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def get_active_tasks_count():
    i = app.control.inspect()
    active = i.active() or {}
    return sum(len(tasks) for tasks in active.values())