import re

def filter_messages_by_keywords(chat_data, keywords, use_regex=False, match_case=True):
    """
    Фильтрует сообщения чата по ключевым словам, используя либо обычный поиск, либо регулярные выражения.

    Args:
        chat_data (list): Список сообщений чата
        keywords (list): Ключевые слова или regex-выражения
        use_regex (bool): Если True, использует regex, иначе обычный поиск
        match_case (bool): Учитывать ли регистр

    Returns:
        list: Отфильтрованные сообщения
    """
    filtered_messages = []
    regex_flags = 0 if match_case else re.IGNORECASE

    # Если используется regex, компилируем выражения заранее
    if use_regex:
        compiled_keywords = [re.compile(kw, regex_flags) for kw in keywords]

    for msg in chat_data:
        text = msg["message"]["body"]

        if use_regex:
            if any(pattern.search(text) for pattern in compiled_keywords):
                filtered_messages.append(msg)
        else:
            if any(kw.lower() in text.lower() for kw in keywords):
                filtered_messages.append(msg)

    return filtered_messages