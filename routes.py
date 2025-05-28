from flask import Blueprint, render_template, request, jsonify, session, send_from_directory, abort
from celery.result import AsyncResult
from config import Config

from app import limiter
from tasks import save_stream_task, run_analysis_task, get_active_tasks_count
from data_collectors.helix_api import extract_vod_id, get_streamer_id
import os
import json

main = Blueprint("main", __name__)
PROJECT_ROOT = os.getenv("PROJECT_ROOT")

@main.route('/', methods=['GET', 'POST'])
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
            return jsonify({"task_id": task.id})
        else:
            return jsonify({"message": "Ошибка: недействительный ID трансляции"}), 400

    return render_template('index.html', message=message, task_id=task_id, vod_url=vod_url)

@main.route('/run_analysis', methods=['POST'])
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
        keywords,
        top_pastes_count,
        emoticons_count
    )

    return jsonify({"status": "success", "task_id": task.id})

@main.route('/check_status/<task_id>', methods=['GET'])
def check_status(task_id):
    task = AsyncResult(task_id)
    if task.state == 'PENDING':
        return jsonify({"status": "pending"})
    elif task.state == 'SUCCESS':
        return jsonify({"status": "success", "result": task.result})
    elif task.state == 'FAILURE':
        return jsonify({"status": "failure", "result": str(task.result)})
    else:
        return jsonify({"status": "unknown"})

@main.route('/get_file/<file_id>', methods=['GET'])
def get_file(file_id):
    storage_dir = os.path.join(PROJECT_ROOT, 'stream_data')
    file_path = os.path.join(storage_dir, f'{file_id}.json')
    if not os.path.exists(file_path):
        abort(404, description="File not found")
    return send_from_directory(storage_dir, f'{file_id}.json', as_attachment=True)


@main.route('/worker_status', methods=['GET'])
@limiter.limit("12 per minute")  # Ограничение на количество запросов
def worker_status():
    try:
        active_count = get_active_tasks_count()
        max_workers = Config.MAX_WORKERS

        return jsonify({
            "active_tasks": active_count,
            "max_workers": max_workers
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route('/about')
def about():
    return render_template('about.html')

@main.route('/faq')
def faq():
    return render_template('faq.html')