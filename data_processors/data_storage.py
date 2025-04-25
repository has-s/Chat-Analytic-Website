import os
import time
from pathlib import Path
from dotenv import load_dotenv

# Загружаем конфигурацию (если нужно)
load_dotenv()
PROJECT_ROOT = os.getenv('PROJECT_ROOT')  # Для теста можно использовать /tmp
STORAGE_PATHS = [os.path.join(PROJECT_ROOT, 'stream_data'), os.path.join(PROJECT_ROOT, 'chats')]

# Настройки
MAX_FOLDER_SIZE_MB = 5000  # Максимальный размер всей папки в МБ
MAX_AGE_DAYS = 30  # Максимальный возраст файлов
MAX_FILE_SIZE_MB = 500  # Максимальный размер одного файла
MIN_FILE_SIZE_MB = 0.001  # Минимальный размер файла для сохранения (например, 1 КБ)


def get_folder_size(path):
    """Возвращает размер папки в мегабайтах."""
    return sum(f.stat().st_size for f in Path(path).rglob("*") if f.is_file()) / (1024 * 1024)


def touch_atime(path):
    """Эмулирует обновление atime на macOS."""
    try:
        current_time = time.time()
        mtime = os.stat(path).st_mtime
        os.utime(path, (current_time, mtime))
    except Exception as e:
        print(f"Не удалось обновить atime для {path}: {e}")


def delete_old_streams(paths=None, max_age_days=MAX_AGE_DAYS,
                       max_folder_size_mb=MAX_FOLDER_SIZE_MB, max_size_mb=MAX_FILE_SIZE_MB,
                       min_size_mb=MIN_FILE_SIZE_MB):
    """Удаляет файлы трансляций, если они старше max_age_days, больше max_size_mb, меньше min_size_mb, или если папка превышает
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

        # Удаляем файлы, которые слишком старые, маленькие или большие
        files = list(storage_dir.iterdir())
        for file in files:
            if file.is_file():
                file_stat = file.stat()
                file_age = now - file_stat.st_atime  # Время последнего доступа
                file_size = file_stat.st_size / (1024 * 1024)  # В МБ

                # Эмулируем обновление atime для macOS
                if os.name == 'posix':  # только для macOS и Linux
                    touch_atime(file)

                # Удаляем файлы, которые слишком старые, маленькие или большие
                if file_age > max_age_seconds or file_size > max_size_mb or file_size < min_size_mb:
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


def create_test_files(directory):
    """Создаёт тестовые файлы для демонстрации."""
    if not Path(directory).exists():
        Path(directory).mkdir(parents=True, exist_ok=True)

    now = time.time()
    # Создадим 3 файла:
    # 1. файл старше 30 дней
    # 2. файл меньше 30 дней, но размер больше лимита
    # 3. пустой файл, который будет удалён

    # Файл 1: старше 30 дней
    old_file = Path(directory) / "old_file.txt"
    with open(old_file, "w") as f:
        f.write("This is a test file.")
    os.utime(old_file, (now - (MAX_AGE_DAYS + 1) * 86400, now - (MAX_AGE_DAYS + 1) * 86400))  # старый файл

    # Файл 2: размер больше лимита
    large_file = Path(directory) / "large_file.txt"
    with open(large_file, "w") as f:
        f.write("This is a large file." * 10000)  # сделаем файл большим
    os.utime(large_file, (now - 10 * 86400, now - 10 * 86400))  # в пределах лимита по времени

    # Файл 3: пустой файл, который будет удалён
    empty_file = Path(directory) / "empty_file.txt"
    with open(empty_file, "w") as f:
        pass  # пустой файл
    os.utime(empty_file, (now - 5 * 86400, now - 5 * 86400))  # в пределах лимита по времени

    # Файл 4: нормальный файл, не для удаления
    normal_file = Path(directory) / "normal_file.txt"
    with open(normal_file, "w") as f:
        f.write("This file should not be deleted.")
    os.utime(normal_file, (now - 5 * 86400, now - 5 * 86400))  # в пределах лимита по времени и размеру


# Тестирование
def test_cleanup():
    test_dir = Path(PROJECT_ROOT) / "stream_data"
    create_test_files(test_dir)

    print("\n--- Перед очисткой ---")
    for f in os.listdir(test_dir):
        print(
            f"Файл: {f}, Размер: {os.path.getsize(os.path.join(test_dir, f)) / (1024 * 1024)} MB, Последний доступ: {time.ctime(os.path.getatime(os.path.join(test_dir, f)))}")

    deleted = delete_old_streams(paths=[str(test_dir)], max_age_days=30, max_folder_size_mb=MAX_FOLDER_SIZE_MB,
                                 max_size_mb=MAX_FILE_SIZE_MB, min_size_mb=MIN_FILE_SIZE_MB)

    print(f"\nУдалено файлов: {deleted}")
    print("\n--- После очистки ---")
    for f in os.listdir(test_dir):
        print(
            f"Файл: {f}, Размер: {os.path.getsize(os.path.join(test_dir, f)) / (1024 * 1024)} MB, Последний доступ: {time.ctime(os.path.getatime(os.path.join(test_dir, f)))}")


if __name__ == "__main__":
    test_cleanup()