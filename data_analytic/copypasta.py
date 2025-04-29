import json
import re
from collections import defaultdict
from difflib import SequenceMatcher
import os
from pathlib import Path
from dotenv import load_dotenv

# === ПАРАМЕТРЫ ===
PASTA_MIN_LENGTH = 10  # Минимальная длина пасты
SIMILARITY_THRESHOLD = 0.8  # Порог схожести для группировки

# Загрузка переменных среды
# Загрузим .env.local.local для локальной разработки
if os.environ.get('FLASK_ENV') == 'development':
    load_dotenv('.env.local')
else:
    load_dotenv('.env.docker')

# Получаем корневой путь проекта из переменной окружения
PROJECT_ROOT = os.getenv("PROJECT_ROOT")

if not PROJECT_ROOT:
    raise ValueError("PROJECT_ROOT не задан в переменных окружения.")

# Функция загрузки чата по stream_id
def load_chat_data(stream_id):
    """Функция загрузки чата по stream_id"""
    # Строим абсолютный путь к файлу
    file_path = Path(PROJECT_ROOT) / "stream_data" / f"{stream_id}.json"

    if not file_path.exists():
        raise FileNotFoundError(f"Файл {file_path} не найден.")

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)["chat"]

# Функция нормализации текста
def normalize_text(text):
    """Приводит текст к форме без пробелов и знаков препинания, но сохраняет регистр"""
    return re.sub(r"[^\w\d]+", "", text)

# Функция для извлечения паст из чата
def extract_pastas(chat_data):
    """Извлекает повторяющиеся пасты из чата"""
    pasta_counter = defaultdict(list)

    for msg in chat_data:
        text = msg["message"]["body"]
        msg_id = msg["_id"]

        if len(text) < PASTA_MIN_LENGTH:
            continue  # Пропускаем короткие фразы

        pasta_counter[text].append(msg_id)

    return {text: ids for text, ids in pasta_counter.items() if len(ids) > 1}

# Функция для группировки паст по схожести
def group_similar_pastas(pasta_data):
    """Группирует пасты по схожести"""
    grouped_pastas = []
    seen = set()

    for base_pasta, message_ids in sorted(pasta_data.items(), key=lambda x: -len(x[1])):  # Сортируем по убыванию
        if base_pasta in seen:
            continue

        base_normalized = normalize_text(base_pasta)
        group = {
            "base_pasta": base_pasta,
            "count": len(message_ids),
            "variants": []
        }

        for other_pasta, other_ids in pasta_data.items():
            if other_pasta in seen or other_pasta == base_pasta:
                continue

            other_normalized = normalize_text(other_pasta)
            similarity = SequenceMatcher(None, base_normalized, other_normalized).ratio()

            if similarity >= SIMILARITY_THRESHOLD:
                group["variants"].append({
                    "text": other_pasta,
                    "count": len(other_ids)
                })
                seen.add(other_pasta)

        grouped_pastas.append(group)
        seen.add(base_pasta)

    return grouped_pastas

# Основная функция для получения паст
def get_pastas_for_stream(stream_id, top_n=None):
    """Основная функция: загружает чат, анализирует пасты и возвращает их отсортированными."""
    chat_data = load_chat_data(stream_id)
    pastas = extract_pastas(chat_data)
    grouped_pastas = group_similar_pastas(pastas)
    return grouped_pastas[:top_n]  # Ограничиваем количество выводимых паст

# === ПРИМЕР ИСПОЛЬЗОВАНИЯ ===
if __name__ == "__main__":
    stream_id = "2406296141"  # ID нужной трансляции
    top_n = 10  # Количество паст для вывода

    # Получение паст
    result = get_pastas_for_stream(stream_id, top_n=top_n)

    # Отображение данных в нужной форме
    print(f"🔍 ТОП-{top_n} ПАСТ:")
    for i, pasta in enumerate(result, 1):
        print(f"{i}. Базовая паста: {pasta['base_pasta']} — Количество: {pasta['count']}")
        if pasta["variants"]:
            print("   🔹 Подпасты:")
            for variant in pasta["variants"]:
                print(f"      - {variant['text']} — Количество: {variant['count']}")