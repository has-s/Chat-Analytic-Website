from flask import Flask, render_template, request, jsonify, session, send_from_directory, abort
from celery.result import AsyncResult
from celery_config import make_celery
from tasks import save_stream_task, run_analysis_task
from data_collectors.helix_api import extract_vod_id, get_streamer_id
import json
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

app = Flask(__name__)

# Используем переменную окружения для секретного ключа
app.secret_key = os.getenv("FLASK_KEY", "default_secret_key")  # Если переменная не найдена, используем дефолтное значение
PROJECT_ROOT = os.getenv("PROJECT_ROOT")

# Конфигурация Celery
app.config.from_object('config.Config')
celery = make_celery()

@app.route('/', methods=['GET', 'POST'])
def index():
    message = None
    task_id = None
    vod_url = ""

    if request.method == 'POST':
        vod_url = request.form.get('vod_url')
        vod_id = extract_vod_id(vod_url)
        streamer_id = get_streamer_id(vod_id)

        if streamer_id is not None:
            session["vod_id"] = vod_id
            task = save_stream_task.apply_async(args=[vod_id])
            return jsonify({"task_id": task.id})  # Возврат JSON-ответа
        else:
            return jsonify({"message": "Ошибка: недействительный ID трансляции"}), 400

    return render_template('index.html', message=message, task_id=task_id, vod_url=vod_url)

@app.route('/run_analysis', methods=['POST'])
def run_analysis():
    metrics = request.form.getlist('metrics')
    top_chatters_count = int(request.form.get('top_chatters_count', 10))
    top_pastes_count = int(request.form.get('top_pastes_count', 10))
    emoticons_count = int(request.form.get('emoticons_count', 10))
    vod_id = session.get("vod_id")

    keywords_raw = request.form.get('keywords', '[]')
    try:
        keywords = json.loads(keywords_raw)
        if not isinstance(keywords, list):
            raise ValueError("Ключевые слова должны быть списком.")
    except (json.JSONDecodeError, ValueError) as e:
        return jsonify({"status": "error", "message": f"Ошибка в ключевых словах: {str(e)}"}), 400

    if not metrics or not vod_id:
        return jsonify({"status": "error", "message": "Отсутствуют метрики или VOD ID"}), 400

    task = run_analysis_task.delay(
        vod_id,
        metrics,
        top_chatters_count,
        keywords,  # <- теперь это список, а не строка
        top_pastes_count,
        emoticons_count
    )

    return jsonify({"status": "success", "task_id": task.id})

@app.route('/check_status/<task_id>', methods=['GET'])
def check_status(task_id):
    task = AsyncResult(task_id, app=celery)
    if task.state == 'PENDING':
        return jsonify({"status": "pending"})
    elif task.state == 'SUCCESS':
        return jsonify({"status": "success", "result": task.result})
    elif task.state == 'FAILURE':
        return jsonify({"status": "failure", "result": str(task.result)})
    else:
        return jsonify({"status": "unknown"})


@app.route('/get_file/<file_id>', methods=['GET'])
def get_file(file_id):
    # Директория, где хранятся файлы
    storage_dir = os.path.join(PROJECT_ROOT, 'stream_data')

    # Формируем путь к файлу на основе идентификатора
    file_path = os.path.join(storage_dir, f'{file_id}.json')  # Например, .json как расширение

    if not os.path.exists(file_path):
        abort(404, description="File not found")

    return send_from_directory(storage_dir, f'{file_id}.json', as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)