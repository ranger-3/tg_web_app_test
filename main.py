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
    <!DOCTYPE html>
    <html lang="ru">

    <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Колесо удачи</title>
    <style>
        body {
        margin: 0;
        height: 100vh;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: radial-gradient(circle at center, #fefefe, #ccc);
        font-family: 'Segoe UI', sans-serif;
        }

        .wheel-wrapper {
        position: relative;
        width: 320px;
        height: 320px;
        }

        .wheel {
        width: 100%;
        height: 100%;
        border-radius: 50%;
        box-shadow:
            0 0 20px rgba(0, 0, 0, 0.2),
            inset 0 0 10px rgba(0, 0, 0, 0.1);
        transform: rotate(0deg);
        }

        .pointer {
        position: absolute;
        top: 2px;
        left: 50%;
        transform: translateX(-50%) rotate(0deg);
        transform-origin: top center;
        width: 12px;
        height: 34px;
        background: linear-gradient(to bottom, #f0d27c, #caa64c, #a67c00);
        border-radius: 6px 6px 60% 60% / 6px 6px 100% 100%;
        border: 1.5px solid #8a6d1d;
        box-shadow:
            0 2px 4px rgba(0, 0, 0, 0.4),
            inset 0 -2px 3px rgba(255, 255, 255, 0.3),
            inset 0 1px 2px rgba(255, 255, 255, 0.2);
        z-index: 10;
        }

        .pointer::after {
        content: "";
        position: absolute;
        top: -6px;
        left: 50%;
        transform: translateX(-50%);
        width: 10px;
        height: 10px;
        background: radial-gradient(circle at center, #eaeaea, #888);
        border: 1px solid #666;
        border-radius: 50%;
        box-shadow:
            0 1px 2px rgba(0, 0, 0, 0.4),
            inset 0 1px 1px rgba(255, 255, 255, 0.5);
        }

        button {
        margin-top: 30px;
        padding: 12px 24px;
        font-size: 18px;
        background-color: #ff6f61;
        color: #fff;
        border: none;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        cursor: pointer;
        transition: background 0.3s ease;
        }

        button:hover {
        background-color: #ff3b2e;
        }
    </style>
    </head>

    <body>

    <div class="wheel-wrapper">
        <canvas id="wheelCanvas" class="wheel" width="300" height="300"></canvas>
        <div id="pointer" class="pointer"></div>
    </div>

    <button onclick="spinWheel()">Крутить!</button>

    <script>
        const canvas = document.getElementById('wheelCanvas');
        const pointer = document.getElementById('pointer');
        const ctx = canvas.getContext('2d');

        const segments = ['5%', '10%', '2%', '15%', '7%'];
        const colors = ['#ffe066', '#ffad60', '#d3d3d3', '#80ed99', '#9ad0f5', '#d3d3d3'];
        const degPerSegment = 360 / segments.length;

        let rotation = 0;
        let velocity = 0;
        let spinning = false;

        function drawWheel() {
        ctx.clearRect(0, 0, 300, 300);
        segments.forEach((label, i) => {
            const start = (i * degPerSegment) * Math.PI / 180;
            const end = ((i + 1) * degPerSegment) * Math.PI / 180;

            // сектор
            ctx.beginPath();
            ctx.moveTo(150, 150);
            ctx.arc(150, 150, 140, start, end);
            ctx.fillStyle = colors[i];
            ctx.fill();
            ctx.strokeStyle = '#fff';
            ctx.lineWidth = 2;
            ctx.stroke();

            // текст
            ctx.save();
            ctx.translate(150, 150);
            ctx.rotate((start + end) / 2);
            ctx.font = 'bold 16px sans-serif';
            ctx.fillStyle = '#333';
            ctx.textAlign = 'right';
            ctx.fillText(label, 120, 5);
            ctx.restore();
        });
        }

        drawWheel();

        function spinWheel() {
        if (spinning) return;
        spinning = true;
        velocity = 15;
        requestAnimationFrame(animate);
        }

        function animate() {
        if (velocity <= 0.1) {
            spinning = false;
            velocity = 0;
            return;
        }

        rotation = (rotation + velocity) % 360;
        velocity *= 0.985; // трение

        canvas.style.transform = `rotate(${rotation}deg)`;

        const angle = Math.sin(rotation / 10) * velocity * 0.2;
        pointer.style.transform = `translateX(-50%) rotate(${angle}deg)`;

        drawWheel();
        requestAnimationFrame(animate);
        }
    </script>

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
