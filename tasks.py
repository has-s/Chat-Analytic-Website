from celery import Celery
from data_processors.stream_compose import collect_stream_data, save_stream_data
from data_processors.analytic_composer import analyze_stream_data

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

        return {
            "status": "success",
            "received_data": input_data["received_data"],
            "analysis_result": analysis_result
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}