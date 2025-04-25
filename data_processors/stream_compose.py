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


def check_existing_data(vod_id):
    """Проверяет, существует ли файл для этого vod_id."""
    file_path = os.path.join(OUTPUT_DIR, f"{vod_id}.json")
    return os.path.exists(file_path)


def get_chat_data(vod_id):
    """Получает чат-данные для известного vod_id из файла."""
    chat_file_path = os.path.join(OUTPUT_DIR, f"{vod_id}.json")

    try:
        # Проверяем, существует ли файл
        if not os.path.exists(chat_file_path):
            print(f"❌ Файл с чатом для VOD {vod_id} не найден.")
            return None

        # Открываем и читаем данные из файла
        with open(chat_file_path, "r", encoding="utf-8") as f:
            chat_data = json.load(f)

        if not chat_data:
            print(f"❌ Чат для VOD {vod_id} пуст.")
            return None

        return chat_data

    except Exception as e:
        print(f"❌ Ошибка при чтении чата для VOD {vod_id}: {e}")
        return None


def collect_stream_data(vod_id):
    """Собирает данные о трансляции, если они ещё не сохранены."""

    # Если данные уже есть, просто сообщаем и выходим
    if check_existing_data(vod_id):
        print(f"⚠️ Данные для {vod_id} уже существуют. Пропускаем сбор.")
        return "exists"  # Если файл существует, возвращаем 'exists'

    # 1. Получаем информацию о VOD
    vod_info = get_times_stream_info(vod_id)
    if not vod_info:
        return None  # Не удалось получить данные о VOD

    # 2. Извлекаем ID стримера
    user_id = get_streamer_id(vod_id)
    if not user_id:
        return None  # Не удалось получить ID стримера

    # 3. Загружаем эмоуты стримера
    emotes = load_emotes(user_id)

    # 4. Получаем чат данных через новую функцию
    chat_data = get_chat_data(vod_id)
    if not chat_data:
        print("💬 Чат не найден. Пробуем скачать...")
        downloaded_chat = download_chat_to_file(vod_id)
        if not downloaded_chat:
            print("❌ Не удалось скачать чат.")
            return None
        chat_data = downloaded_chat  # обновим переменную

    # 5. Извлекаем категории (смена игр и разделов)
    categories = process_url(vod_id)

    # 6. Формируем итоговые данные
    stream_data = {
        "video_id": vod_id,
        "user_id": user_id,
        "vod_info": vod_info,
        "emotes": emotes,
        "chat": chat_data,
        "categories": categories  # Добавленные категории
    }

    return stream_data  # Возвращаем данные о стриме


def save_stream_data(vod_id, stream_data):
    """Сохраняет данные о трансляции в JSON-файл с именем, соответствующим vod_id."""

    # Путь к файлу будет использовать vod_id как имя файла
    output_path = os.path.join(OUTPUT_DIR, f"{vod_id}.json")

    # Проверяем, существует ли файл для данного vod_id
    if check_existing_data(vod_id):
        print(f"⚠️ Данные для {vod_id} уже существуют. Пропускаем сохранение.")
        return output_path  # Если файл существует, возвращаем путь к существующему файлу

    try:
        # Сохраняем данные в JSON-файл
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(stream_data, f, ensure_ascii=False, indent=4)

        print(f"💾 Данные сохранены в {output_path}")
        return output_path
    except IOError as e:
        print(f"❌ Ошибка при сохранении файла: {e}")
        return None


# Пример использования
if __name__ == "__main__":
    video_id = "2434728985"
    result = collect_stream_data(video_id)

    if result == "exists":
        print("✅ Данные для данного VOD уже существуют. Завершаем работу.")
    elif result:
        save_stream_data(video_id, result)  # Сохраняем данные
        print("🎉 Сбор данных завершён.")
    else:
        print("❌ Сбор данных не удался.")