import json
from filter import filter_messages_by_keywords

from data_processors.stream_compose import get_chat_data

def analyze_chat_activity(chat_data, keywords=None, use_regex=False, match_case=True):
    """
    Анализирует активность чата и возвращает данные для графика.

    Args:
        chat_data (list): Список сообщений чата, включающий категории.
        keywords (list, optional): Список ключевых слов или regex-выражений.
        use_regex (bool): Если True, искать через regex.
        match_case (bool): Учитывать ли регистр.

    Returns:
        dict: Данные для построения графика.
    """
    messages_per_minute = {}
    keyword_messages_per_minute = {} if keywords else {}  # Если нет ключевых слов, то не считаем
    category_intervals = []

    # Извлекаем категории из chat_data
    categories = chat_data.get('categories', [])
    for cat in categories:
        start_time = (cat["end_time"] - cat["duration"]) // 60
        end_time = cat["end_time"] // 60
        category_intervals.append((start_time, end_time, cat["category"]))

    # Фильтруем сообщения по ключевым словам (если они есть)
    if keywords:
        filtered_chat = filter_messages_by_keywords(chat_data["chat"], keywords, use_regex, match_case)
    else:
        filtered_chat = chat_data["chat"]

    # Подсчет всех сообщений в минуту
    for msg in chat_data["chat"]:
        minute = msg["content_offset_seconds"] // 60
        messages_per_minute[minute] = messages_per_minute.get(minute, 0) + 1

    # Подсчет сообщений по ключевым словам (если они есть)
    if keywords:
        for msg in filtered_chat:
            minute = msg["content_offset_seconds"] // 60
            keyword_messages_per_minute[minute] = keyword_messages_per_minute.get(minute, 0) + 1

    # Заполняем нулями минуты, где нет сообщений по ключевым словам (если нужны такие данные)
    min_time = min(messages_per_minute.keys())
    max_time = max(messages_per_minute.keys())

    for minute in range(min_time, max_time + 1):
        if minute not in keyword_messages_per_minute:
            keyword_messages_per_minute[minute] = 0

    return {
        "messages_per_minute": messages_per_minute,
        "keyword_messages_per_minute": keyword_messages_per_minute,
        "category_intervals": category_intervals,
    }


def analyze_emotes(chat_data, top_n=None, include_platform=True):
    """
    Считает общее количество использований каждого эмоута за стрим с опцией добавления платформы.

    Args:
        chat_data (dict): Словарь с ключами 'chat' (список сообщений) и 'emotes' (эмоуты по платформам).
        top_n (int, optional): Кол-во топ эмоутов, которые нужно вернуть. Если None — возвращает все.
        include_platform (bool): Включить ли информацию о платформе (ffz, bttv, 7tv).

    Returns:
        list[dict]: Список словарей с данными по эмоутам: имя, количество, ссылка (и платформа при include_platform=True).
    """
    emotes_data = chat_data.get("emotes", {})
    messages = chat_data.get("chat", [])

    # Собираем имя -> {url, платформа}
    emote_info = {}
    for platform, emotes in emotes_data.items():
        for e in emotes:
            emote_info[e["name"]] = {
                "url": e["url"],
                "platform": platform
            }

    emote_counts = {}

    for msg in messages:
        try:
            text = msg["message"]["body"]
        except (KeyError, TypeError):
            continue

        for emote_name in emote_info:
            if emote_name in text:
                emote_counts[emote_name] = emote_counts.get(emote_name, 0) + 1

    # Сортировка
    sorted_emotes = sorted(emote_counts.items(), key=lambda item: item[1], reverse=True)

    if top_n is not None:
        sorted_emotes = sorted_emotes[:top_n]

    # Формируем результат
    result = []
    for name, count in sorted_emotes:
        emote_data = {
            "name": name,
            "count": count,
            "url": emote_info[name]["url"]
        }
        if include_platform:
            emote_data["platform"] = emote_info[name]["platform"]

        result.append(emote_data)

    return result


if __name__ == "__main__":
    video_id = "2406296141"
    data = get_chat_data(video_id)

    print(analyze_emotes(data))
