from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import os
import httpx

app = FastAPI()

# ---- LLM config (from env) ----
LLM_TOKEN = os.getenv("LLM_TOKEN")             # OpenRouter key (set on Render)
LLM_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
LLM_MODEL = os.getenv("LLM_MODEL", "openrouter/free")  # model name

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
    """
    Call OpenRouter chat completion and return model's reply text.
    If token missing, simple echo.
    """
    if not LLM_TOKEN:
        now = datetime.now().strftime("%H:%M:%S")
        return f"[{now}] Robot: You said -> {user_text}"

    headers = {
        "Authorization": f"Bearer {LLM_TOKEN}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://botproject-esp32",
        "X-Title": "ESP32 CampusBot",
    }

    body = {
        "model": LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a friendly small campus desk robot. "
                    "Reply briefly (1-2 sentences), in simple English; "
                    "user id may be used just for personalization."
                ),
            },
            {
                "role": "user",
                "content": f"[user_id={user_id}] {user_text}",
            },
        ],
    }

    async with httpx.AsyncClient(timeout=25.0) as client:
        resp = await client.post(LLM_ENDPOINT, headers=headers, json=body)
        # If OpenRouter returns any HTTP error, raise here
        resp.raise_for_status()
        data = resp.json()
        reply = data["choices"][0]["message"]["content"]
        return reply

@app.get("/")
async def root():
    return {"status": "ok", "message": "ESP32 bot backend running with LLM"}

@app.post("/bot", response_model=BotResponse)
async def bot_endpoint(req: BotRequest):
    # 1) get AI reply from LLM, but never crash
    try:
        reply_text = await call_llm(req.user_text, req.user_id)
    except Exception as e:
        # Debug log for Render
        print("LLM error:", repr(e))
        now = datetime.now().strftime("%H:%M:%S")
        reply_text = (
            f"[{now}] (fallback) I am having trouble with my AI brain, "
            f"but I heard you said: {req.user_text}"
        )

    # 2) simple emotion classifier on reply text
    emotion = classify_emotion(reply_text)

    # 3) placeholder audio URL
    fake_audio_url = "https://example.com/no-audio-yet"

    return BotResponse(
        reply_text=reply_text,
        audio_url=fake_audio_url,
        emotion=emotion,
    )
