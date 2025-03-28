from flask import Flask, render_template, request, jsonify
from celery.result import AsyncResult
from celery_config import make_celery
from tasks import save_stream_task
from data_collectors.helix_api import extract_vod_id, get_streamer_id

app = Flask(__name__)

# Конфигурация Celery
app.config.from_object('config.Config')
celery = make_celery()

@app.route('/', methods=['GET', 'POST'])
def index():
    message = None  # Сообщение для отображения на странице
    result = None  # Результат задачи
    task_id = None  # ID задачи для отслеживания состояния

    if request.method == 'POST':
        vod_url = request.form.get('vod_url')  # Получаем URL трансляции (может быть разного формата)

        # Извлечение vod_id из URL
        vod_id = extract_vod_id(vod_url)
        streamer_id = get_streamer_id(vod_id)

        if streamer_id is not None:
            # Запуск задачи Celery
            task = save_stream_task.apply_async(args=[vod_id])
            task_id = task.id

            # Просто возвращаем ID задачи и не показываем сообщение сразу
        else:
            message = "Ошибка: недействительный ID трансляции!"

    return render_template('index.html', message=message, task_id=task_id)

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