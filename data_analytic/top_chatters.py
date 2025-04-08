from collections import Counter

def get_top_chatters(data, top_n=10):
    """Возвращает топ-N самых активных чаттеров"""
    chat_data = data.get("chat", [])  # Извлекаем список сообщений из данных
    user_counts = Counter()

    # Проходим по каждому сообщению в чате
    for msg in chat_data:
        # Проверяем, что msg является словарем и что он содержит нужные ключи
        if isinstance(msg, dict) and "commenter" in msg:
            commenter_name = msg["commenter"].get("name")  # Получаем имя комментатора
            if commenter_name:
                user_counts[commenter_name] += 1

    return user_counts.most_common(top_n)

'''
# Пример использования
if __name__ == "__main__":
    top_chatters = get_top_chatters(data, top_n=3)
    print("Топ чаттеров:")
    for rank, (name, count) in enumerate(top_chatters, 1):
        print(f"{rank}. {name} — {count} сообщений")
'''