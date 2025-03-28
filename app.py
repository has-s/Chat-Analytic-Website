from flask import Flask, render_template, request
from celery_config import make_celery
from tasks import start_analysis_task
from data_collectors.helix_api import extract_vod_id, get_streamer_id

app = Flask(__name__)
app.config.from_object('config.Config')

# Настроим Celery
celery = make_celery()

@app.route('/', methods=['GET', 'POST'])
def index():
    message = None

    if request.method == 'POST':
        vod_url = request.form.get('vod_url')

        # Извлечение vod_id из URL
        vod_id = extract_vod_id(vod_url)
        streamer_id = get_streamer_id(vod_id)

        if streamer_id is not None:
            message = f"Трансляция найдена: {vod_id}!"
        else:
            message = "Ошибка: недействительный ID трансляции!"

    return render_template('index.html', message=message)

if __name__ == "__main__":
    app.run(debug=True)