import re, os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from data_collectors.helix_api import get_stream_duration  # Функция для получения длительности видео

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [category_parser] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("category_parser")

# Загрузим .env.local.local для локальной разработки
if os.environ.get('FLASK_ENV') == 'development':
    load_dotenv('.env.local')
else:
    load_dotenv('.env.docker')

CHROMEDRIVER_PATH = os.getenv('CHROMEDRIVER_PATH')

def parse_data(video_id):
    """Собирает текстовую информацию о видео с Twitch VOD."""

    service = Service(CHROMEDRIVER_PATH)
    options = Options()

    # Настройки Selenium
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--incognito')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--lang=en-US')
    options.add_experimental_option("prefs", {"intl.accept_languages": "en,en-US"})

    driver = webdriver.Chrome(service=service, options=options)
    url = f"https://www.twitch.tv/videos/{video_id}"

    try:
        logger.info(f"🚀 Открываем страницу {url}")
        driver.get(url)

        # Проверка на недоступность видео
        try:
            WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.XPATH,
                                                "//*[contains(text(), \"Sorry. Unless you've got a time machine, that content is unavailable.\")]"))
            )
            logger.warning(f"⚠️ Видео {video_id} недоступно.")
            return None
        except Exception:
            pass

        # Нажатие кнопки "Start Watching", если она есть
        try:
            start_button = WebDriverWait(driver, 1).until(
                EC.element_to_be_clickable((By.XPATH,
                                            "//div[@data-a-target='tw-core-button-label-text' and contains(text(), 'Start Watching')]"))
            )
            start_button.click()
            logger.info("▶️ Нажата кнопка 'Start Watching'.")
        except Exception:
            pass

        # Нажатие кнопки "Continue Watching" при возрастном ограничении
        try:
            continue_button = WebDriverWait(driver, 1).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continue Watching')]"))
            )
            continue_button.click()
            logger.info("🔞 Нажата кнопка 'Continue Watching'.")
        except Exception:
            pass

        # Получаем HTML страницы
        WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        html = driver.page_source
        logger.info(f"✅ Страница {url} загружена успешно.")

    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке страницы: {e}")
        return None
    finally:
        driver.quit()

    # Обработка HTML с помощью BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    return soup.get_text(separator=' ', strip=True)


def extract_info(text):
    """Извлекает категорию и временные метки из текста."""
    share_pattern = re.compile(r'Share\s*(.*?)\s*·')
    volume_pattern = re.compile(r'Volume(.*?)Volume', re.DOTALL)

    share_info = None
    volume_info = None

    # Извлекаем текущую категорию
    share_match = share_pattern.search(text)
    if share_match:
        share_info = share_match.group(1).strip()

    # Извлекаем переходы категорий
    volume_match = volume_pattern.search(text)
    if volume_match:
        volume_info_segment = volume_match.group(1).strip()
        volume_info_segment = re.sub(r'\bleft\s+', '', volume_info_segment)
        timestamps = re.findall(r'\b\d{2}:\d{2}:\d{2}\b', volume_info_segment)
        if timestamps:
            last_timestamp = timestamps[-1]
            last_index = volume_info_segment.rfind(last_timestamp)
            volume_info = volume_info_segment[last_index + len(last_timestamp):].strip()

    # Обработка переходов категорий
    result = []
    if volume_info:
        items = volume_info.split(' ')
        i = 0

        while i < len(items):
            category = []
            while i < len(items) and not items[i].isdigit():
                category.append(items[i])
                i += 1

            time_str = []
            while i < len(items) and (
                    items[i].isdigit() or items[i] in ['hour', 'hours', 'minute', 'minutes', 'second', 'seconds']):
                time_str.append(items[i])
                i += 1

            if category and time_str:
                result.append((' '.join(category), ' '.join(time_str)))

    return share_info, result if result else None


def time_to_seconds(time_str):
    """Преобразует строку с временем в секунды."""
    hours = int(re.search(r'(\d+)\s*hour', time_str).group(1)) if 'hour' in time_str else 0
    minutes = int(re.search(r'(\d+)\s*minute', time_str).group(1)) if 'minute' in time_str else 0
    seconds = int(re.search(r'(\d+)\s*second', time_str).group(1)) if 'second' in time_str else 0
    return hours * 3600 + minutes * 60 + seconds


def accumulate_seconds(pairs):
    """Накапливает секунды для каждой категории."""
    accumulated = []
    total_seconds = 0

    for category, time_str in pairs:
        seconds = time_to_seconds(time_str)
        total_seconds += seconds
        accumulated.append((category, total_seconds))

    return accumulated


def format_categories(transitions):
    """Добавляет поле duration к списку категорий."""
    categories = []

    for i, (category, end_time) in enumerate(transitions):
        if i == 0:
            duration = end_time  # Первая категория длится с 0 до `end_time`
        else:
            duration = end_time - transitions[i - 1][1]  # Разница с предыдущей категорией

        categories.append({
            "category": category,
            "end_time": end_time,
            "duration": duration
        })

    return categories


def process_url(video_id):
    """Основной процесс сбора данных по ID видео."""
    logger.info(f"🚀 Начало обработки видео {video_id}.")
    page_text = parse_data(video_id)

    if not page_text:
        logger.error(f"❌ Не удалось загрузить данные для видео {video_id}.")
        return None

    current_category, volume_pairs = extract_info(page_text)

    if volume_pairs:
        accumulated = accumulate_seconds(volume_pairs)
        logger.info(f"📊 Найдено {len(accumulated)} переходов категорий.")
        return format_categories(accumulated)
    else:
        stream_duration = get_stream_duration(video_id)
        if stream_duration:
            return [{"category": current_category, "end_time": stream_duration, "duration": stream_duration}]
        else:
            return None


# Пример использования
if __name__ == "__main__":
    video_id = "2376580226"
    transitions = process_url(video_id)
    if transitions:
        for cat in transitions:
            logger.info(f"📜 {cat}")