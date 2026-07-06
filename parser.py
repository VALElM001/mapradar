import json
import requests
from datetime import datetime, timedelta

# Два независимых RSS-источника для большей стабильности
URLS = [
    "https://api.rss2json.com/v1/api.json?rss_url=https%3A%2F%2Fnews.rambler.ru%2Frss%2Fincidents%2F",
    "https://api.rss2json.com/v1/api.json?rss_url=https%3A%2F%2Fwww.vedomosti.ru%2Frss%2Fnews"
]

# Соответствие корней слов ISO-кодам регионов
REGION_MAPPING = {
    "курск": "RU-KUR",
    "орлов": "RU-ORL",
    "твер": "RU-TVE",
    "тульс": "RU-TUL",
    "калуж": "RU-KLU",
    "москов": "RU-MOS",
    "подмосков": "RU-MOS",
    "белг": "RU-BEL",
    "брян": "RU-BRY",
    "ворон": "RU-VOR",
    "ростов": "RU-ROS",
    "краснодар": "RU-KDA",
    "крым": "RU-CR"
}

def main():
    # 1. Загружаем текущую базу алертов или создаем пустую
    try:
        with open('alerts.json', 'r', encoding='utf-8') as f:
            alerts = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        alerts = {}

    # 2. Собираем новости из источников
    for url in URLS:
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                items = response.json().get("items", [])
                for item in items:
                    title = item.get("title", "").lower()
                    description = item.get("description", "").lower()
                    full_text = title + " " + description
                    
                    # Маркеры опасности и отбоя
                    is_alert = any(w in full_text for w in ["бпла", "беспилотник", "воздушная тревога", "ракетная опасность", "атака бпла"])
                    is_clear = any(w in full_text for w in ["отбой", "ликвидиров", "сбит", "подавлен"])
                    
                    if not is_alert and not is_clear:
                        continue
                        
                    # Проверяем регионы
                    for key, iso in REGION_MAPPING.items():
                        if key in full_text:
                            # Если это чистая атака/тревога без упоминания отбоя
                            if is_alert and not is_clear:
                                alerts[iso] = {
                                    "alert": 1,
                                    "time": datetime.utcnow().isoformat(),
                                    "title": item.get("title", "")
                                }
                            # Если в тексте фигурирует отбой
                            elif is_clear:
                                alerts[iso] = {
                                    "alert": 0,
                                    "time": datetime.utcnow().isoformat(),
                                    "title": item.get("title", "")
                                }
        except Exception as e:
            print(f"Ошибка при запросе к {url}: {e}")

    # 3. Авто-отбой: если тревога висит дольше 6 часов, снимаем её (на случай, если СМИ не дали новость об отбое)
    now = datetime.utcnow()
    for iso, info in list(alerts.items()):
        if info.get("alert") == 1:
            try:
                alert_time = datetime.fromisoformat(info.get("time"))
                if now - alert_time > timedelta(hours=6):
                    alerts[iso] = {
                        "alert": 0,
                        "time": now.isoformat(),
                        "title": "Автоматическое снятие по таймауту"
                    }
            except Exception:
                pass

    # 4. Сохраняем обновленный файл
    with open('alerts.json', 'w', encoding='utf-8') as f:
        json.dump(alerts, f, ensure_ascii=False, indent=2)
    print("Файл alerts.json успешно обновлен.")

if __name__ == "__main__":
    main()
