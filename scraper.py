import json
import os
import re
from datetime import datetime
import requests

def get_stock_futures():
    url = "https://www.taifex.com.tw/cht/2/stockLists"
    try:
        res = requests.get(url, timeout=10)
        futures_codes = set(re.findall(r"\b\d{4}\b", res.text))
        return futures_codes
    except Exception:
        return set()

def fetch_twse_punish():
    url = "https://www.twse.com.tw/rwd/zh/announcement/punish?response=json"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        items = []
        if data.get("stat") == "OK":
            for row in data.get("data", []):
                code, name = row[1].strip(), row[2].strip()
                period = row[3].strip()
                detail = row[4].strip()
                items.append({
                    "market": "上市",
                    "code": code,
                    "name": name,
                    "period": period,
                    "detail": detail,
                    "interval": "20分" if "20分" in detail else ("5分" if "5分" in detail else "一般")
                })
        return items
    except Exception as e:
        return []

def fetch_tpex_punish():
    url = "https://www.tpex.org.tw/web/bulletin/disposal/disposal_result.php?l=zh-tw"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        items = []
        for row in data.get("aaData", []):
            code, name = row[1].strip(), row[2].strip()
            period = row[3].strip()
            detail = row[4].strip()
            items.append({
                "market": "上櫃",
                "code": code,
                "name": name,
                "period": period,
                "detail": detail,
                "interval": "20分" if "20分" in detail else ("5分" if "5分" in detail else "一般")
            })
        return items
    except Exception as e:
        return []

def main():
    futures_set = get_stock_futures()
    records = fetch_twse_punish() + fetch_tpex_punish()
    
    history_file = "history_punish.json"
    history = {}
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            try:
                history = json.load(f)
            except:
                pass

    today_str = datetime.now().strftime("%Y-%m-%d")
    processed_list = []

    for item in records:
        code = item["code"]
        item["has_futures"] = code in futures_set
        occurrences = history.get(code, [])
        item["is_repeat"] = len(occurrences) >= 1
        item["punish_count"] = len(occurrences) + 1
        
        if today_str not in occurrences:
            occurrences.append(today_str)
        history[code] = occurrences[-5:]

        processed_list.append(item)

    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    output = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(processed_list),
        "data": processed_list
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
