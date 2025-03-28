import os
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
PROJECT_ROOT = os.getenv('PROJECT_ROOT')
STORAGE_PATHS = [os.path.join(PROJECT_ROOT, 'stream_data'), os.path.join(PROJECT_ROOT, 'chats')]

MAX_FOLDER_SIZE_MB = 5000  # Максимальный размер всей папки в МБ
MAX_AGE_DAYS = 30  # Максимальный возраст файлов
MAX_FILE_SIZE_MB = 500  # Максимальный размер одного файла


def get_folder_size(path):
    """Возвращает размер папки в мегабайтах."""
    return sum(f.stat().st_size for f in Path(path).rglob("*") if f.is_file()) / (1024 * 1024)


def delete_old_streams(paths=None, max_age_days=MAX_AGE_DAYS,
                       max_folder_size_mb=MAX_FOLDER_SIZE_MB, max_size_mb=MAX_FILE_SIZE_MB):

    """Удаляет файлы трансляций, если они старше max_age_days, больше max_size_mb или если папка превышает
    max_folder_size_mb."""
    if paths is None:
        paths = STORAGE_PATHS
    now = time.time()
    max_age_seconds = max_age_days * 86400  # 30 дней в секундах
    deleted = 0

    for storage_path in paths:
        storage_dir = Path(storage_path)
        if not storage_dir.exists():
            continue

        # Удаляем файлы, которые слишком старые или большие
        files = list(storage_dir.iterdir())
        for file in files:
            if file.is_file():
                file_stat = file.stat()
                file_age = now - file_stat.st_mtime  # Время последнего изменения
                file_size = file_stat.st_size / (1024 * 1024)  # В МБ

                if file_age > max_age_seconds or file_size > max_size_mb:
                    os.remove(file)
                    deleted += 1

        # Проверяем, не превышен ли размер папки
        while get_folder_size(storage_path) > max_folder_size_mb:
            oldest_file = min(storage_dir.iterdir(), key=lambda f: f.stat().st_mtime, default=None)
            if oldest_file and oldest_file.is_file():
                os.remove(oldest_file)
                deleted += 1

    return deleted
