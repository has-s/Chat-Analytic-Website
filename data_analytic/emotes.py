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
