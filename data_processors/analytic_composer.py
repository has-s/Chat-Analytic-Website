from data_processors.stream_compose import get_chat_data
from data_analytic.analyse import analyze_chat_activity
from data_analytic.top_chatters import get_top_chatters
from data_analytic.copypasta import get_pastas_for_stream
from data_analytic.filter import filter_messages_by_keywords
from data_analytic.emotes import analyze_emotes


def analyze_stream_data(result):
    # Получаем данные о чате
    chat_data = get_chat_data(result["received_data"]["vod_id"])

    # Настроим параметры аналитики
    metrics = result["received_data"]["metrics"]
    top_chatters_count = result["received_data"]["top_chatters_count"]
    top_pastes_count = result["received_data"]["top_pastes_count"]
    emoticons_count = result["received_data"]["emoticons_count"]
    keywords = result["received_data"]["keywords"]

    analysis_result = {}

    # Анализируем топ-чатеров, если указано в метриках
    if "top_chatters" in metrics:
        analysis_result["top_chatters"] = get_top_chatters(chat_data, top_n=top_chatters_count)

    # Анализируем ключевые слова, если указано
    if "keywords_search" in metrics:
        analysis_result["keywords_search"] = filter_messages_by_keywords(chat_data, keywords)

    # Анализируем пасты, если указано
    if "top_pastes" in metrics:
        analysis_result["top_pastes"] = get_pastas_for_stream(result["received_data"]["vod_id"], top_n=top_pastes_count)

    # Анализируем эмотиконы, если указано
    if "top_emoticons" in metrics:
        analysis_result["top_emoticons"] = analyze_emotes(chat_data, top_n=emoticons_count)

    # Анализируем активность чата, если указано
    if "chat_activity" in metrics:
        analysis_result["chat_activity"] = analyze_chat_activity(chat_data, keywords=keywords)

    return analysis_result


# Пример использования
if __name__ == "__main__":
    input_data = {
        "received_data": {
            "vod_id": "2425707027",
            "metrics": ["top_chatters", "top_pastes", "top_emoticons", "chat_activity"], #"top_pastes", "top_emoticons", "chat_activity"
            "top_chatters_count": 10,
            "top_pastes_count": 10,
            "emoticons_count": 10,
            "keywords": "omegalul"
        },
        "status": "success"
    }

    result = analyze_stream_data(input_data)
    print(result)