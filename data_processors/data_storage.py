# data_processors/data_storage.py

import os
import time
from pathlib import Path

def get_folder_size(path):
    """Возвращает размер папки в мегабайтах."""
    return sum(f.stat().st_size for f in Path(path).rglob("*") if f.is_file()) / (1024 * 1024)

def delete_old_streams(paths=None, max_age_days=30, max_folder_size_mb=5000, max_size_mb=500):
    """Удаляет файлы трансляций, если они старше max_age_days, больше max_size_mb или если папка превышает
    max_folder_size_mb."""
    if paths is None:
        paths = ['/tmp/stream_data', '/tmp/chats']

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
                file_age = now - file_stat.st_atime  # Время последнего доступа
                file_size = file_stat.st_size / (1024 * 1024)  # В МБ

                # Удаляем файлы, которые слишком старые или большие
                if file_age > max_age_seconds or file_size > max_size_mb:
                    try:
                        os.remove(file)
                        deleted += 1
                        print(f"Удалён файл: {file}")
                    except Exception as e:
                        print(f"Не удалось удалить файл {file}: {e}")

        # Проверяем, не превышен ли размер папки
        while get_folder_size(storage_path) > max_folder_size_mb:
            oldest_file = min(storage_dir.iterdir(), key=lambda f: f.stat().st_mtime, default=None)
            if oldest_file and oldest_file.is_file():
                try:
                    os.remove(oldest_file)
                    deleted += 1
                    print(f"Удалён старый файл: {oldest_file}")
                except Exception as e:
                    print(f"Не удалось удалить файл {oldest_file}: {e}")

    return deleted