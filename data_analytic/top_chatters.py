from collections import Counter

def get_top_chatters(chat_data, top_n=10):
    """Возвращает топ-N самых активных чаттеров"""
    user_counts = Counter(msg["commenter"]["name"] for msg in chat_data)
    return user_counts.most_common(top_n)