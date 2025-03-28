import requests
from flask import Flask, request, jsonify, render_template
from data_collectors.helix_api import extract_vod_id, get_streamer_id  # Импортируем нужные функции

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    message = None  # Сообщение для отображения на странице

    if request.method == 'POST':
        vod_url = request.form.get('vod_url')  # Получаем URL трансляции (может быть разного формата)

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