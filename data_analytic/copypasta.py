import json
import re
from collections import defaultdict
from difflib import SequenceMatcher

# === ПАРАМЕТРЫ ===
PASTA_MIN_LENGTH = 10  # Минимальная длина пасты
SIMILARITY_THRESHOLD = 0.8  # Порог схожести для группировки

import os
from pathlib import Path
import json
from dotenv import load_dotenv

# Загрузка переменных среды
load_dotenv()

# Получаем корневой путь проекта из переменной окружения
PROJECT_ROOT = os.getenv("PROJECT_ROOT")

if not PROJECT_ROOT:
    raise ValueError("PROJECT_ROOT не задан в переменных окружения.")


# Функция загрузки чата по stream_id
def load_chat_data(stream_id):
    """Функция загрузки чата по stream_id (заглушка, нужно реализовать отдельно)."""
    # Строим абсолютный путь к файлу
    file_path = Path(PROJECT_ROOT) / "stream_data" / f"{stream_id}.json"

    if not file_path.exists():
        raise FileNotFoundError(f"Файл {file_path} не найден.")

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)["chat"]


# Получаем путь к проекту из переменной окружения (или по умолчанию).
PROJECT_ROOT = os.getenv("PROJECT_ROOT", Path(__file__).resolve().parent)

def load_chat_data(stream_id):
    """Загружает данные чата по stream_id."""
    file_path = Path(PROJECT_ROOT) / "stream_data" / f"{stream_id}.json"

    if not file_path.exists():
        raise FileNotFoundError(f"Файл {file_path} не найден.")

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)["chat"]


def normalize_text(text):
    """Приводит текст к форме без пробелов и знаков препинания, но сохраняет регистр"""
    return re.sub(r"[^\w\d]+", "", text)


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
            "messages": message_ids,
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
                    "count": len(other_ids),
                    "messages": other_ids
                })
                seen.add(other_pasta)

        grouped_pastas.append(group)
        seen.add(base_pasta)

    return grouped_pastas


def get_pastas_for_stream(stream_id):
    """Основная функция: загружает чат, анализирует пасты и возвращает их отсортированными."""
    chat_data = load_chat_data(stream_id)
    pastas = extract_pastas(chat_data)
    grouped_pastas = group_similar_pastas(pastas)
    return grouped_pastas


# === ПРИМЕР ИСПОЛЬЗОВАНИЯ ===
if __name__ == "__main__":
    stream_id = "2406296141"  # ID нужной трансляции
    result = get_pastas_for_stream(stream_id)

    print("🔍 ТОП-10 ПАСТ:")
    for i, pasta in enumerate(result[:10], 1):
        print(f"{i}. {pasta['base_pasta']} ({pasta['count']} повторов)")
        if pasta["variants"]:
            print("   🔹 Варианты:")
            for variant in pasta["variants"]:
                print(f"      - {variant['text']} ({variant['count']} повторов)")