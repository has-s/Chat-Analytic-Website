import requests
import json
import os
from dotenv import load_dotenv
from logging_config import setup_logger

# Настройка логирования
logger = setup_logger("chat_downloader")

# Загрузка переменных среды
# Загрузим .env.local.local для локальной разработки
if os.environ.get('FLASK_ENV') == 'development':
    load_dotenv('.env.local')
else:
    load_dotenv('.env.docker')

PROJECT_ROOT = os.getenv('PROJECT_ROOT')
CHAT_CLIENT_ID = os.getenv("CHAT_CLIENT_ID")
CHAT_CLIENT_SHA = os.getenv("CHAT_CLIENT_SHA")

if not CHAT_CLIENT_ID or not CHAT_CLIENT_SHA:
    logger.critical("❌ Переменные среды CHAT_CLIENT_ID и CHAT_CLIENT_SHA не заданы.")
    raise ValueError("Отсутствуют необходимые переменные среды.")

# Используем PROJECT_ROOT для указания пути к директории чатов
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'chats')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_chat_file_path(video_id):
    """Возвращает путь к файлу чата."""
    return os.path.join(OUTPUT_DIR, f"{video_id}.json")


def load_chat_from_file(video_id):
    """Загружает чат из файла, если он существует."""
    chat_file = get_chat_file_path(video_id)
    if os.path.exists(chat_file):
        logger.info(f"📂 Чат для {video_id} найден. Загружаем данные из файла.")
        try:
            with open(chat_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"❌ Ошибка при загрузке чата из файла: {e}")
            return None
    return None


def download_chat_to_file(video_id, start=0, force_download=False):
    """
    Скачивает чат, если его нет в файле, и возвращает данные.

    Args:
        video_id (str): ID видео.
        start (int): Начальное время в секундах.
        force_download (bool): Если True, загружает чат заново, даже если он уже есть.

    Returns:
        list: Список загруженных комментариев.
    """

    # Проверяем, существует ли уже чат в файле
    if not force_download:
        existing_chat = load_chat_from_file(video_id)
        if existing_chat is not None:
            return existing_chat

    logger.info(f"🚀 Начало загрузки чата для видео {video_id}. (Принудительно: {force_download})")
    headers = {"Client-ID": CHAT_CLIENT_ID}
    comments_dict = {}
    cursor = None

    while True:
        payload = {
            "operationName": "VideoCommentsByOffsetOrCursor",
            "variables": {"videoID": video_id, "contentOffsetSeconds": start},
            "extensions": {
                "persistedQuery": {"version": 1, "sha256Hash": CHAT_CLIENT_SHA}
            }
        }
        if cursor:
            payload["variables"]["cursor"] = cursor

        try:
            response = requests.post("https://gql.twitch.tv/gql", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка при запросе данных: {e}")
            return None

        comments = data.get("data", {}).get("video", {}).get("comments", {}).get("edges", [])
        if not comments:
            logger.warning("⚠️ Комментарии не найдены или достигнут конец данных.")
            break

        for comment in comments:
            node = comment["node"]
            if not node.get("commenter"):
                logger.warning("⚠️ Пропущен комментарий без информации о пользователе.")
                continue

            comment_id = node["id"]
            if comment_id not in comments_dict:
                # Извлекаем бейджи пользователя (если есть)
                badges = [
                    {"set_id": badge["setID"], "version": badge["version"]}
                    for badge in node["message"].get("userBadges", [])
                ]

                comments_dict[comment_id] = {
                    "_id": comment_id,
                    "created_at": node["createdAt"],
                    "content_offset_seconds": node["contentOffsetSeconds"],
                    "commenter": {
                        "display_name": node["commenter"]["displayName"].strip(),
                        "_id": node["commenter"]["id"],
                        "name": node["commenter"]["login"]
                    },
                    "message": {
                        "body": "".join(frag["text"] for frag in node["message"]["fragments"] if frag["text"]),
                        "user_color": node["message"]["userColor"],
                        "badges": badges  # Добавляем бейджи
                    }
                }

        page_info = data.get("data", {}).get("video", {}).get("comments", {}).get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            logger.info("🏁 Достигнут конец чата.")
            break

        cursor = comments[-1]["cursor"]

    unique_comments = list(comments_dict.values())
    logger.info(f"🔍 Загружено {len(unique_comments)} уникальных комментариев.")

    # Сохраняем в файл
    output_path = get_chat_file_path(video_id)
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(unique_comments, f, ensure_ascii=False, indent=4)
        logger.info(f"✅ Чат сохранён в {output_path}.")
    except IOError as e:
        logger.error(f"❌ Ошибка при сохранении файла: {e}")
        return None

    return unique_comments


# Пример использования
if __name__ == "__main__":
    video_id = "2406296141"
    force_reload = True  # Установи True, чтобы загрузить чат заново

    comments = download_chat_to_file(video_id, force_download=force_reload)

    if comments:
        logger.info(f"🎉 Всего получено {len(comments)} комментариев.")
    else:
        logger.warning("❌ Чат не был загружен.")