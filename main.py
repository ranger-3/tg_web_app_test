from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import hmac
import hashlib
import time
import random
from fastapi.responses import HTMLResponse

app = FastAPI()

# Разрешаем CORS для фронта
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # на проде лучше указывать конкретный домен
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔐 Секрет Telegram WebApp Token (тот же, что у бота, но без "bot")
BOT_TOKEN = "7571256577:AAFGCDLSMXqo-6-akUISJlDM4_8wWmwYhVo"
SECRET_KEY = hashlib.sha256(BOT_TOKEN.encode()).digest()

# 🎯 Призы на колесе
SECTORS = [
    {"label": "5% скидка", "code": "DISCOUNT5"},
    {"label": "10% скидка", "code": "DISCOUNT10"},
    {"label": "Пусто", "code": None},
    {"label": "15% скидка", "code": "DISCOUNT15"},
    {"label": "Промокод на кофе", "code": "COFFEE"},
    {"label": "Пусто", "code": None},
]


class SpinRequest(BaseModel):
    init_data: str


class SpinResponse(BaseModel):
    sector: str
    code: str | None


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
      <head><title>Колесо удачи</title></head>
      <body>
        <h1>Привет! Тут будет колесо 🚀</h1>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
      </body>
    </html>
    """


def verify_init_data(init_data: str) -> bool:
    try:
        data_check_string, hash_received = init_data.split("&hash=")
        data_bytes = data_check_string.encode()
        hmac_obj = hmac.new(SECRET_KEY, data_bytes, hashlib.sha256)
        calc_hash = hmac_obj.hexdigest()
        return hmac.compare_digest(calc_hash, hash_received)
    except Exception:
        return False


@app.post("/spin", response_model=SpinResponse)
async def spin(request: SpinRequest):
    if not verify_init_data(request.init_data):
        raise HTTPException(status_code=403, detail="Invalid initData")

    # 🎲 Выбираем случайный сектор
    selected = random.choice(SECTORS)
    return SpinResponse(sector=selected["label"], code=selected["code"])


@app.get("/sectors")
async def get_sectors():
    return [s["label"] for s in SECTORS]
