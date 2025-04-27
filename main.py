from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
from fastapi.responses import HTMLResponse
from fastapi import Request

logs = [] 
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Подключаем Mongo
client = MongoClient("mongodb://localhost:27017/")
collection = client["sanctions_db"]["sanctions_list"]

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, country: str = None, source: str = None):
    query = {}
    if country:
        query["Country"] = {"$regex": country, "$options": "i"}
    if source:
        query["Source"] = source

    data = list(collection.find(query, {"_id": 0}))
    return templates.TemplateResponse("index.html", {"request": request, "records": data})

def log_message(level, message):
    logs.append(f"{level}: {message}")
    print(f"{level}: {message}")

# Первый лог при запуске
log_message("INFO", "Application started")

@app.get("/logs", response_class=HTMLResponse)
async def get_logs_page():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Server Logs</title>
        <style>
            body { font-family: monospace; background: #111; color: #eee; padding: 10px; }
            .log { white-space: pre-wrap; }
            .INFO { color: #00FF00; }
            .WARNING { color: #FFFF00; }
            .ERROR { color: #FF3333; }
        </style>
    </head>
    <body>
        <h2>Server Logs</h2>
        <div id="logs" class="log"></div>

        <script>
            async function fetchLogs() {
                const response = await fetch('/logs_data');
                const text = await response.text();
                document.getElementById('logs').innerHTML = text;
                window.scrollTo(0, document.body.scrollHeight);
            }
            setInterval(fetchLogs, 1000); // обновление раз в 1 сек
            fetchLogs();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/logs_data", response_class=HTMLResponse)
async def get_logs_data():
    styled_logs = []
    for log in logs[-200:]:  # максимум последние 200 записей
        if "INFO" in log:
            styled_logs.append(f'<div class="INFO">{log}</div>')
        elif "WARNING" in log:
            styled_logs.append(f'<div class="WARNING">{log}</div>')
        elif "ERROR" in log:
            styled_logs.append(f'<div class="ERROR">{log}</div>')
        else:
            styled_logs.append(f"<div>{log}</div>")
    return "<br>".join(styled_logs)