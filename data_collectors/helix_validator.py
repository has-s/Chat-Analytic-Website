import requests
import os
from dotenv import load_dotenv
from logging_config import setup_logger

# Логгер
logger = setup_logger("helix_validator")

# Загрузка переменных окружения
load_dotenv()
PROJECT_ROOT = os.getenv('PROJECT_ROOT')
CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")

TOKEN_FILE = os.path.join(PROJECT_ROOT, 'config/.helix_token')
VALIDATION_URL = "https://id.twitch.tv/oauth2/validate"


def save_token_to_file(token):
    """Сохраняет токен в файл."""
    try:
        with open(TOKEN_FILE, "w") as file:
            file.write(token)
        logger.info(f"💾 Токен сохранён в файл {TOKEN_FILE}")
    except IOError as e:
        logger.error(f"❌ Ошибка при сохранении токена в файл: {e}")


def load_token_from_file():
    """Загружает токен из файла, если он существует."""
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r") as file:
                return file.read().strip()
        except IOError as e:
            logger.error(f"❌ Ошибка при загрузке токена из файла: {e}")
    return None


def is_token_valid(token):
    """Проверяет валидность токена с помощью Helix API."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(VALIDATION_URL, headers=headers)
        if response.status_code == 200:
            logger.info("✅ Токен валиден")
            return True
        logger.warning(f"⚠️ Токен недействителен: {response.status_code} - {response.json().get('message', 'Нет сообщения')}")
        return False
    except requests.RequestException as e:
        logger.error(f"❌ Ошибка проверки токена: {e}")
        return False


def get_helix_token(client_id, client_secret):
    """Получает Bearer токен. Если есть валидный токен в файле — использует его."""
    existing_token = load_token_from_file()
    if existing_token and is_token_valid(existing_token):
        logger.info("✅ Используется сохранённый и валидный токен")
        return existing_token

    url = "https://id.twitch.tv/oauth2/token"
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }

    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        data = response.json()
        token = data.get('access_token')

        if token:
            logger.info("✅ Новый токен успешно получен")
            save_token_to_file(token)
            return token
        logger.error("❌ Ошибка: Токен не найден в ответе")
        return None
    except requests.RequestException as e:
        logger.error(f"❌ Ошибка при получении токена: {e}")
        return None


if __name__ == "__main__":
    if not CLIENT_ID or not CLIENT_SECRET:
        logger.critical("🚫 Переменные TWITCH_CLIENT_ID или TWITCH_CLIENT_SECRET не заданы.")
        exit(1)

    token = get_helix_token(CLIENT_ID, CLIENT_SECRET)
    if token:
        logger.info(f"📁 Путь сохранения токена: {TOKEN_FILE}")
    else:
        logger.error("❌ Токен не был получен.")