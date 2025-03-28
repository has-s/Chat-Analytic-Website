from filter import filter_messages_by_keywords

def analyze_chat_activity(chat_data, category_data, keywords=None, use_regex=False, match_case=True):
    """
    Анализирует активность чата и возвращает данные для графика.

    Args:
        chat_data (list): Список сообщений чата
        category_data (list): Список категорий
        keywords (list, optional): Список ключевых слов или regex-выражений.
        use_regex (bool): Если True, искать через regex.
        match_case (bool): Учитывать ли регистр.

    Returns:
        dict: Данные для построения графика.
    """
    messages_per_minute = {}
    keyword_messages_per_minute = {}
    category_intervals = []

    filtered_chat = filter_messages_by_keywords(chat_data, keywords, use_regex, match_case) if keywords else chat_data

    # Заполняем данные по категориям
    for cat in category_data:
        start_time = (cat["end_time"] - cat["duration"]) // 60
        end_time = cat["end_time"] // 60
        category_intervals.append((start_time, end_time, cat["category"]))

    # Подсчет сообщений
    for msg in chat_data:
        minute = msg["content_offset_seconds"] // 60
        messages_per_minute[minute] = messages_per_minute.get(minute, 0) + 1

    # Подсчет сообщений по ключевым словам
    for msg in filtered_chat:
        minute = msg["content_offset_seconds"] // 60
        keyword_messages_per_minute[minute] = keyword_messages_per_minute.get(minute, 0) + 1

    # Заполняем нулями минуты, где нет ключевых слов
    min_time = min(messages_per_minute.keys())
    max_time = max(messages_per_minute.keys())

    for minute in range(min_time, max_time + 1):
        if minute not in keyword_messages_per_minute:
            keyword_messages_per_minute[minute] = 0

    return {
        "messages_per_minute": messages_per_minute,
        "keyword_messages_per_minute": keyword_messages_per_minute,
        "category_intervals": category_intervals,
        "unique_categories": list(set(cat["category"] for cat in category_data))
    }

def analyze_emotes(chat_data, emotes_data):
    """
    Анализирует использование эмоутов в чате.

    Args:
        chat_data (list): Список сообщений чата.
        emotes_data (dict): Словарь доступных эмоутов стримера.

    Returns:
        dict: Данные об использовании эмоутов.
    """
    emote_stats = {}

    for msg in chat_data:
        text = msg["message"]["body"]
        user = msg["commenter"]["name"]
        timestamp = msg["content_offset_seconds"]

        # Проверяем, какие эмоуты есть в тексте
        for emote in emotes_data:
            if emote in text:
                if emote not in emote_stats:
                    emote_stats[emote] = {
                        "count": 0,
                        "messages": [],
                        "users": set(),
                        "timestamps": []
                    }

                emote_stats[emote]["count"] += 1
                emote_stats[emote]["messages"].append(text)
                emote_stats[emote]["users"].add(user)
                emote_stats[emote]["timestamps"].append(timestamp)

    # Преобразуем set в list для сериализации
    for emote in emote_stats:
        emote_stats[emote]["users"] = list(emote_stats[emote]["users"])

    return emote_stats