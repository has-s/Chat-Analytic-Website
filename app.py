from flask import Flask, render_template, request, jsonify, session
from celery.result import AsyncResult
from celery_config import make_celery
from tasks import save_stream_task, run_analysis_task
from data_collectors.helix_api import extract_vod_id, get_streamer_id

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Для работы с сессиями

# Конфигурация Celery
app.config.from_object('config.Config')
celery = make_celery()

@app.route('/', methods=['GET', 'POST'])
def index():
    message = None  # Сообщение для отображения на странице
    task_id = None  # ID задачи для отслеживания состояния
    vod_url = ""  # Устанавливаем пустую строку по умолчанию

    if request.method == 'POST':
        vod_url = request.form.get('vod_url')  # Получаем URL трансляции

        # Извлечение vod_id из URL
        vod_id = extract_vod_id(vod_url)
        streamer_id = get_streamer_id(vod_id)

        if streamer_id is not None:
            # Сохраняем VOD ID в сессию
            session["vod_id"] = vod_id

            # Запуск задачи Celery
            task = save_stream_task.apply_async(args=[vod_id])
            task_id = task.id
        else:
            message = "Ошибка: недействительный ID трансляции"

    return render_template('index.html', message=message, task_id=task_id, vod_url=vod_url)

@app.route('/run_analysis', methods=['POST'])
def run_analysis():
    metrics = request.form.getlist('metrics')
    top_chatters_count = int(request.form.get('top_chatters_count', 10))
    keywords = request.form.get('keywords', "")
    top_pastes_count = int(request.form.get('top_pastes_count', 10))
    emoticons_count = int(request.form.get('emoticons_count', 10))

    vod_id = session.get("vod_id")  # Подставляем VOD ID из сессии

    if not metrics or not vod_id:
        return jsonify({"status": "error", "message": "Отсутствуют метрики или VOD ID"}), 400

    # Запуск задачи
    task = run_analysis_task.delay(vod_id, metrics, top_chatters_count, keywords, top_pastes_count, emoticons_count)
    return jsonify({"status": "success", "task_id": task.id})

@app.route('/check_status/<task_id>', methods=['GET'])
def check_status(task_id):
    task = AsyncResult(task_id, app=celery)
    if task.state == 'PENDING':
        return jsonify({"status": "pending"})
    elif task.state == 'SUCCESS':
        return jsonify({"status": "success", "result": task.result})
    elif task.state == 'FAILURE':
        return jsonify({"status": "failure", "result": task.result})
    else:
        return jsonify({"status": "unknown"})

if __name__ == "__main__":
    app.run(debug=True)