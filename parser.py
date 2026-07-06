import json
import requests
import re
from datetime import datetime

# Агрегатор новостей/уведомлений, который отдает данные без блокировок
DATA_URL = "https://api.rss2json.com/v1/api.json?rss_url=https%3A%2F%2Fnews.rambler.ru%2Frss%2Fincidents%2F"

# Маппинг регионов на ISO-коды (для карты мира формат ISO обычно двухсимвольный или трехсимвольный)
# В GeoJSON мира Россия обычно идет как целая страна (RU), либо разбита на регионы.
# Если используем карту мира с разбивкой по странам, подсвечивать будем саму Россию (RU), либо конкретные ISO регионов.
REGION_MAPPING = {
    "курск": "RU-KUR", "орловск": "RU-ORL", "тверск": "RU-TVE",
    "тульск": "RU-TUL", "калужск": "RU-KLU", "московск": "RU-MOS",
    "белгород": "RU-BEL", "брянск": "RU-BRY", "воронеж": "RU-VOR"
}

def main():
    try:
        with open('alerts.json', 'r', encoding='utf-8') as f:
            alerts = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        alerts = {}

    try:
        response = requests.get(DATA_URL, timeout=10)
        if response.status_code == 200:
            items = response.json().get("items", [])
            
            for item in items:
                title = item.get("title", "").lower()
                description = item.get("description", "").lower()
                full_text = title + " " + description
                
                # Ищем маркеры опасности
                is_alert = "бпла" in full_text or "воздушная тревога" in full_text or "ракетная опасность" in full_text
                is_clear = "отбой" in full_text
                
                if not is_alert and not is_clear:
                    continue
                
                for key, iso in REGION_MAPPING.items():
                    if key in full_text:
                        if is_alert and not is_clear:
                            alerts[iso] = {"alert": 1, "time": datetime.utcnow().isoformat()}
                        elif is_clear:
                            alerts[iso] = {"alert": 0, "time": datetime.utcnow().isoformat()}
            
            with open('alerts.json', 'w', encoding='utf-8') as f:
                json.dump(alerts, f, ensure_ascii=False, indent=2)
            print("Данные успешно обновлены.")
        else:
            print(f"Ошибка запроса: {response.status_code}")
    except Exception as e:
        print(f"Ошибка парсинга: {e}")

if __name__ == "__main__":
    main()
