import requests
import pandas as pd
import xml.etree.ElementTree as ET
import json
from io import StringIO
from pymongo import MongoClient
from datetime import datetime

def log(msg):
    with open("logs.txt", "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        f.write(f"{timestamp} {msg}\n")
    print(msg)

def download_file(url):
    response = requests.get(url)
    if response.status_code == 200 and response.text.strip():
        return response.text
    else:
        log(f"❌ Ошибка загрузки {url}: {response.status_code} или пустой ответ")
        return None

def parse_csv(data):
    """Парсинг CSV-файла, очищаем поле Country."""
    df = pd.read_csv(StringIO(data), usecols=[0, 1, 3], names=["ID", "Name", "Country"], skiprows=1)
    
    # Очищаем поле Country: убираем всё после первой скобки [
    df["Country"] = df["Country"].str.split("[").str[0].str.strip()
    
    # Добавляем пустую колонку Date
    df["Date"] = None
    
    return df


def parse_xml(data):
    try:
        root = ET.fromstring(data)
        records = []
        for entity in root.findall(".//Entity"):
            name = entity.find("Name").text if entity.find("Name") is not None else "Unknown"
            country = entity.find("Country").text if entity.find("Country") is not None else "Unknown"
            date = entity.find("Date").text if entity.find("Date") is not None else "Unknown"
            records.append({"Name": name, "Country": country, "Date": date})
        return pd.DataFrame(records)
    except ET.ParseError as e:
        log(f"❌ Ошибка парсинга XML: {e}")
        return pd.DataFrame()

def clean_data(df):
    df.drop_duplicates(inplace=True)
    df.dropna(subset=["Name", "Country"], inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

def save_to_mongo(df):
    client = MongoClient("mongodb://localhost:27017/")
    db = client["sanctions_db"]
    collection = db["sanctions_list"]
    data = df.to_dict(orient="records")
    collection.delete_many({})  # 💣 Очищаем перед загрузкой
    collection.insert_many(data)
    log(f"✅ Загружено {len(data)} записей в MongoDB")

def process_sanctions():
    sources = {
        "US": {
            "url": "https://www.treasury.gov/ofac/downloads/sdn.csv",
            "format": "csv"
        },
        "UK": {
            "url": "https://assets.publishing.service.gov.uk/media/67e51de1bb6002588a90d5d3/UK_Sanctions_List.xml",
            "format": "xml"
        }
    }

    all_data = []

    for source, info in sources.items():
        log(f"🔄 Загрузка {source}...")
        data = download_file(info["url"])
        if data:
            if info["format"] == "csv":
                df = parse_csv(data)
            elif info["format"] == "xml":
                df = parse_xml(data)
            else:
                log(f"⚠️ Неизвестный формат: {info['format']}")
                continue

            if not df.empty:
                df["Source"] = source
                all_data.append(df)

    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        cleaned_df = clean_data(combined_df)
        save_to_mongo(cleaned_df)
        cleaned_df.to_csv("sanctions_list_cleaned.csv", index=False, encoding="utf-8")
        log("📄 CSV файл 'sanctions_list_cleaned.csv' успешно сохранен.")
    else:
        log("❌ Ошибка: данные пустые")

if __name__ == "__main__":
    process_sanctions()
