import time
from celery import Celery
from data_processors.stream_compose import collect_stream_data, save_stream_data

# Пример создания Celery приложения
app = Celery('tasks', broker='pyamqp://guest@localhost//')


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