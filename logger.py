import logging
from datetime import datetime
from pymongo import MongoClient

# Настройка MongoDB клиента
client = MongoClient("mongodb://localhost:27017/")
db = client["sanctions_db"]
logs_collection = db["app_logs"]

class MongoDBHandler(logging.Handler):
    def emit(self, record):
        log_entry = {
            "timestamp": datetime.now(),
            "level": record.levelname,
            "message": record.getMessage(),
            "source": "sanctions_app"
        }
        logs_collection.insert_one(log_entry)

# Настройка логгера
logger = logging.getLogger("sanctions_app")
logger.setLevel(logging.INFO)
logger.addHandler(MongoDBHandler())

def get_logs(limit=100):
    return list(logs_collection.find().sort("timestamp", -1).limit(limit))