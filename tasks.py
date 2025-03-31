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

@app.task(bind=True)
def run_analysis_task(self, vod_id, metrics, top_chatters_count=10, keywords="", top_pastes_count=10, emoticons_count=10):
    try:
        # Заглушка - возвращаем полученные данные
        received_data = {
            "vod_id": vod_id,
            "metrics": metrics,
            "top_chatters_count": top_chatters_count,
            "keywords": keywords,
            "top_pastes_count": top_pastes_count,
            "emoticons_count": emoticons_count,
        }
        return {'status': 'success', 'received_data': received_data}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}