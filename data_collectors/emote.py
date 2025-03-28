import requests
from logging_config import setup_logger
import json

# Настройка логирования
logger = setup_logger("emote")

def fetch_ffz_emotes(channel_id):
    """Получает эмоции FrankerFaceZ для указанного канала."""
    url = f"https://api.frankerfacez.com/v1/room/id/{channel_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        emotes = []
        for set_data in data.get("sets", {}).values():
            for emote in set_data.get("emoticons", []):
                emotes.append({
                    "name": emote["name"],
                    "url": emote["urls"].get("1", list(emote["urls"].values())[0])
                })

        logger.info(f"✅ Найдено {len(emotes)} эмоций FFZ для канала {channel_id}.")
        return emotes

    except requests.exceptions.HTTPError as e:
        logger.error(f"❌ HTTP ошибка при запросе FFZ: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Ошибка сети при запросе FFZ: {e}")
    except KeyError:
        logger.warning(f"⚠️ Некорректный ответ API FFZ для {channel_id}.")

    return []


def fetch_bttv_emotes(channel_id):
    """Получает эмоции BetterTTV для указанного канала."""
    url = f"https://api.betterttv.net/3/cached/users/twitch/{channel_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        emotes = [
            {"name": e["code"], "url": f"https://cdn.betterttv.net/emote/{e['id']}/1x"}
            for e in data.get("channelEmotes", []) + data.get("sharedEmotes", [])
        ]

        logger.info(f"✅ Найдено {len(emotes)} эмоций BTTV для канала {channel_id}.")
        return emotes

    except requests.exceptions.HTTPError as e:
        logger.error(f"❌ HTTP ошибка при запросе BTTV: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Ошибка сети при запросе BTTV: {e}")

    return []


def fetch_7tv_emotes(channel_id):
    """Получает эмоции 7TV для указанного канала."""
    url = f"https://7tv.io/v3/users/twitch/{channel_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        emotes = [
            {"name": e["name"], "url": f"https://cdn.7tv.app/emote/{e['id']}/1x"}
            for e in data.get("emote_set", {}).get("emotes", [])
        ]

        logger.info(f"✅ Найдено {len(emotes)} эмоций 7TV для канала {channel_id}.")
        return emotes

    except requests.exceptions.HTTPError as e:
        logger.error(f"❌ HTTP ошибка при запросе 7TV: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Ошибка сети при запросе 7TV: {e}")

    return []


def load_emotes(channel_id):
    """Загружает все эмоции (FFZ, BTTV, 7TV) для указанного канала."""
    emotes = {"ffz": [], "bttv": [], "7tv": []}

    logger.info(f"🚀 Начало загрузки эмоций для канала {channel_id}...")

    emotes["ffz"] = fetch_ffz_emotes(channel_id)
    if not emotes["ffz"]:
        logger.warning(f"⚠️ Эмоции FFZ для канала {channel_id} не найдены.")

    emotes["bttv"] = fetch_bttv_emotes(channel_id)
    if not emotes["bttv"]:
        logger.warning(f"⚠️ Эмоции BTTV для канала {channel_id} не найдены.")

    emotes["7tv"] = fetch_7tv_emotes(channel_id)
    if not emotes["7tv"]:
        logger.warning(f"⚠️ Эмоции 7TV для канала {channel_id} не найдены.")

    logger.info(f"🎉 Загрузка эмоций завершена: FFZ={len(emotes['ffz'])}, BTTV={len(emotes['bttv'])}, 7TV={len(emotes['7tv'])}.")
    return emotes


if __name__ == "__main__":
    channel_id = "53815140"  # Пример ID канала
    emotes = load_emotes(channel_id)
    print(json.dumps(emotes, indent=4, ensure_ascii=False))