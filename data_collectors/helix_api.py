import requests
import os
import re
from dotenv import load_dotenv
from logging_config import setup_logger
from data_collectors.helix_validator import get_helix_token

# Логгер
logger = setup_logger("helix_api")

# Загрузка переменных окружения
load_dotenv()
CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
BASE_URL = 'https://api.twitch.tv/helix'

# Получаем токен через helix_validator
TOKEN = get_helix_token(CLIENT_ID, CLIENT_SECRET)
if not TOKEN:
    logger.error("❌ Не удалось получить токен доступа. Завершение работы.")
    exit(1)


def get_headers():
    """Создает заголовки для запросов к Helix API."""
    return {
        'Authorization': f'Bearer {TOKEN}',
        'Client-Id': CLIENT_ID
    }
def get_streamer_id(vod_id):
    """Получает ID стримера по ID VOD."""
    vod_data = get_times_stream_info(vod_id)
    if vod_data and "user_id" in vod_data:
        return vod_data["user_id"]
    return None

def make_request(endpoint, params=None):
    """Выполняет запрос к API Twitch Helix и обрабатывает ошибки."""
    try:
        response = requests.get(f'{BASE_URL}{endpoint}', headers=get_headers(), params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP ошибка: {e.response.status_code} - {e.response.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка сети: {e}")
    except ValueError:
        logger.error("Некорректный JSON-ответ.")
    return None


def get_user_info(username):
    """Получает информацию о пользователе Twitch по его логину."""
    logger.info(f"🔍 Получаем информацию о пользователе {username}")
    user_info = make_request('/users', {'login': username})
    if user_info and user_info.get('data'):
        user = user_info['data'][0]
        logger.info(f"👤 Пользователь найден: {user['display_name']} (ID: {user['id']})")
        return user
    logger.warning(f"⚠️ Пользователь '{username}' не найден.")
    return None


def get_times_stream_info(vod_id):
    """Получает информацию о VOD по его ID."""
    logger.info(f"🔍 Получаем информацию о VOD с ID {vod_id}")
    vod_info = make_request('/videos', {'id': vod_id})
    if vod_info and vod_info.get('data'):
        logger.info(f"📼 Найдено видео: {vod_info['data'][0]['title']}")
        return vod_info['data'][0]
    logger.warning(f"⚠️ Видео с ID '{vod_id}' не найдено.")
    return None


def get_stream_info(username):
    """Получает информацию о текущей трансляции пользователя."""
    logger.info(f"🔍 Получаем информацию о текущей трансляции {username}")
    stream_info = make_request('/streams', {'user_login': username})
    if stream_info and stream_info.get('data'):
        logger.info(f"📡 Трансляция активна: {stream_info['data'][0]['title']}")
        return stream_info['data'][0]
    logger.info(f"ℹ️ Трансляция у {username} не активна.")
    return None


def get_channel_info(broadcaster_id):
    """Получает информацию о канале по ID ведущего."""
    logger.info(f"🔍 Получаем информацию о канале с ID {broadcaster_id}")
    channel_info = make_request('/channels', {'broadcaster_id': broadcaster_id})
    if channel_info and channel_info.get('data'):
        logger.info(f"📺 Канал: {channel_info['data'][0]['broadcaster_name']}")
        return channel_info['data'][0]
    logger.warning(f"⚠️ Канал с ID '{broadcaster_id}' не найден.")
    return None


def get_past_streams(user_id, limit=10):
    """Получает список прошедших трансляций пользователя."""
    logger.info(f"🔍 Получаем последние {limit} трансляций для пользователя с ID {user_id}")
    past_streams = make_request('/videos', {'user_id': user_id, 'type': 'archive', 'first': limit})
    if past_streams and past_streams.get('data'):
        logger.info(f"📚 Найдено {len(past_streams['data'])} прошедших трансляций.")
        return past_streams['data']
    logger.warning(f"⚠️ Прошедшие трансляции для ID '{user_id}' не найдены.")
    return []


def get_stream_duration(vod_id):
    """
    Получает длительность стрима в секундах.

    Args:
        vod_id (str): ID трансляции.

    Returns:
        int: Длительность стрима в секундах или None, если данные недоступны.
    """
    vod_info = get_times_stream_info(vod_id)

    if not vod_info or "duration" not in vod_info:
        return None  # Если нет данных, возвращаем None

    duration_str = vod_info["duration"]  # Берём строку длительности
    match = re.match(r'(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?', duration_str)

    if not match:
        return None  # Если формат не подошёл

    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    seconds = int(match.group(3)) if match.group(3) else 0

    return hours * 3600 + minutes * 60 + seconds


if __name__ == "__main__":
    example_username = "Olesha"

    user_info = get_user_info(example_username)
    if user_info:
        logger.info(f"👤 Пользователь: {user_info}")

        user_id = user_info['id']
        past_streams = get_past_streams(user_id)
        if past_streams:
            for stream in past_streams:
                logger.info(f"📼 Прошлая трансляция: {stream['title']} ({stream['id']})")
        else:
            logger.warning(f"⚠️ Нет прошедших трансляций для {example_username}.")