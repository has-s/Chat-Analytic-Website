from data_analytic.filter import filter_messages_by_keywords
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

if __name__ == "__main__":
    stream_id = "2425707027"  # ID нужной трансляции
    keywords = [""]  # Пример ключевых слов для фильтрации

    # Получение данных чата для трансляции
    chat_data = get_chat_data(stream_id)  # Предполагается, что get_chat_data возвращает необходимые данные

    # Анализ активности чата
    result = analyze_chat_activity(chat_data, keywords=keywords)

    # Отображение результатов
    print("📊 Результаты анализа активности чата:")
    print("💬 Сообщения по минутам:")
    for minute, count in result["messages_per_minute"].items():
        print(f"  Минутa {minute}: {count} сообщений")

    print("\n🔑 Сообщения по ключевым словам:")
    for minute, count in result["keyword_messages_per_minute"].items():
        print(f"  Минутa {minute}: {count} сообщений с ключевыми словами")

    print("\n📅 Интервалы категорий:")
    for start_time, end_time, category in result["category_intervals"]:
        print(f"  Категория: {category} — с {start_time} мин по {end_time} мин")