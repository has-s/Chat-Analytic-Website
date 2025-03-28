from flask import Flask, render_template, request
from celery.result import AsyncResult
from celery_config import make_celery  # Импортируйте make_celery
from tasks import take_stream_data
from data_collectors.helix_api import extract_vod_id, get_streamer_id

app = Flask(__name__)

# Конфигурация Celery
app.config.from_object('config.Config')
celery = make_celery()

@app.route('/', methods=['GET', 'POST'])
def index():
    message = None  # Сообщение для отображения на странице
    result = None  # Результат задачи

    if request.method == 'POST':
        vod_url = request.form.get('vod_url')  # Получаем URL трансляции

        # Извлечение vod_id из URL
        vod_id = extract_vod_id(vod_url)
        streamer_id = get_streamer_id(vod_id)

        if streamer_id is not None:
            # Запуск задачи Celery
            task = take_stream_data.apply_async(args=[vod_id])

            # Ожидание результата
            result = task.get(timeout=30)

            message = f"Трансляция найдена: {vod_id}! Результат анализа: {result}"
        else:
            message = "Ошибка: недействительный ID трансляции!"

    return render_template('index.html', message=message, result=result)

if __name__ == "__main__":
    app.run(debug=True)