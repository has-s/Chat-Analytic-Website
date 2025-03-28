import json
import os
from dotenv import load_dotenv
from data_collectors.helix_api import get_times_stream_info, get_streamer_id
from data_collectors.emote import load_emotes
from data_collectors.chat_download import download_chat_to_file
from data_collectors.category_parser import process_url  # Добавлен парсер категорий


load_dotenv()
PROJECT_ROOT = os.getenv('PROJECT_ROOT')

# Директория для сохранения данных
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'stream_data')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def check_existing_data(video_id):
    """Проверяет, существует ли уже файл с данными трансляции."""
    output_path = os.path.join(OUTPUT_DIR, f"{video_id}.json")
    return os.path.exists(output_path)


def collect_stream_data(video_id):
    """Собирает данные о трансляции, если они ещё не сохранены."""

    # Если данные уже есть, просто сообщаем и выходим
    if check_existing_data(video_id):
        print(f"⚠️ Данные для {video_id} уже существуют. Пропускаем сбор.")
        return "exists"

    # 1. Получаем информацию о VOD
    vod_info = get_times_stream_info(video_id)
    if not vod_info:
        return None  # Не удалось получить данные о VOD

    # 2. Извлекаем ID стримера
    user_id = get_streamer_id(video_id)
    if not user_id:
        return None  # Не удалось получить ID стримера

    # 3. Загружаем эмоуты стримера
    emotes = load_emotes(user_id)

    # 4. Загружаем чат трансляции
    chat_data = download_chat_to_file(video_id)

    # 5. Извлекаем категории (смена игр и разделов)
    categories = process_url(video_id)

    # 6. Формируем итоговые данные
    stream_data = {
        "video_id": video_id,
        "user_id": user_id,
        "vod_info": vod_info,
        "emotes": emotes,
        "chat": chat_data,
        "categories": categories  # Добавленные категории
    }

    return stream_data


def save_stream_data(video_id, stream_data):
    """Сохраняет данные о трансляции в JSON-файл, если они ещё не сохранены."""
    output_path = os.path.join(OUTPUT_DIR, f"{video_id}.json")

    if check_existing_data(video_id):
        print(f"⚠️ Файл {output_path} уже существует. Сохранение отменено.")
        return output_path

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(stream_data, f, ensure_ascii=False, indent=4)
        print(f"💾 Данные сохранены в {output_path}")
        return output_path
    except IOError as e:
        print(f"❌ Ошибка при сохранении файла: {e}")
        return None


# Пример использования
if __name__ == "__main__":
    video_id = "2406296141"
    data = collect_stream_data(video_id)

    if data == "exists":
        print("✅ Данные уже существуют. Завершаем работу.")
    elif data:
        save_stream_data(video_id, data)
        print("🎉 Сбор данных завершён.")
    else:
        print("❌ Сбор данных не удался.")