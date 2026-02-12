from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import os
import httpx
from dotenv import load_dotenv

# Load .env (for local dev; Render pe env UI se aayega)
load_dotenv()

app = FastAPI()

LLM_TOKEN = os.getenv("LLM_TOKEN")
LLM_MODEL = os.getenv("LLM_MODEL", "mistral-7b-instruct:free")
LLM_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

class BotRequest(BaseModel):
    user_text: str
    user_id: str

class BotResponse(BaseModel):
    reply_text: str
    audio_url: str
    emotion: str

def classify_emotion(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["happy", "great", "awesome", "love"]):
        return "HAPPY"
    if any(w in t for w in ["sad", "angry", "bad", "upset"]):
        return "SAD"
    return "NEUTRAL"

async def call_llm(user_text: str, user_id: str) -> str:
    # Agar token missing hai to simple echo
    if not LLM_TOKEN:
        now = datetime.now().strftime("%H:%M:%S")
        return f"[{now}] Robot: You said -> {user_text}"

    headers = {
        "Authorization": f"Bearer {LLM_TOKEN}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://esp32-bot",   # koi bhi string
        "X-Title": "ESP32 CampusBot",
    }

    body = {
        "model": LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a friendly small campus desk robot. "
                    "Reply in 1-2 short sentences, simple English."
                ),
            },
            {
                "role": "user",
                "content": f"[user_id={user_id}] {user_text}",
            },
        ],
    }

    async with httpx.AsyncClient(timeout=12.0) as client:
        resp = await client.post(LLM_ENDPOINT, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

@app.get("/")
async def root():
    return {"status": "ok", "message": "ESP32 bot backend running with OpenRouter LLM"}

@app.post("/bot", response_model=BotResponse)
async def bot_endpoint(req: BotRequest):
    try:
        reply_text = await call_llm(req.user_text, req.user_id)
    except Exception as e:
        print("LLM error:", repr(e))
        now = datetime.now().strftime("%H:%M:%S")
        reply_text = (
            f"[{now}] (fallback) My AI brain has an issue, "
            f"but I heard you said: {req.user_text}"
        )

    emotion = classify_emotion(reply_text)
    fake_audio_url = ""

    return BotResponse(
        reply_text=reply_text,
        audio_url=fake_audio_url,
        emotion=emotion,
    )
