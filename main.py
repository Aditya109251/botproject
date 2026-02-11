from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import os

app = FastAPI()

# ---- API key (abhi use nahi kar rahe, sirf read kar rahe) ----
LLM_TOKEN = os.getenv("LLM_TOKEN")  # ye .env me wali key hai

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
    if any(w in t for w in ["sad", "angry", "bad"]):
        return "SAD"
    return "NEUTRAL"

@app.get("/")
async def root():
    # simple check endpoint
    return {"status": "ok", "message": "ESP32 bot backend running"}

@app.post("/bot", response_model=BotResponse)
async def bot_endpoint(req: BotRequest):
    # yahan future me LLM call karenge; abhi sirf echo + time
    now = datetime.now().strftime("%H:%M:%S")
    reply = f"[{now}] Robot: You said -> {req.user_text}"

    emotion = classify_emotion(reply)

    # abhi audio nahi, sirf dummy URL
    fake_audio_url = "https://example.com/no-audio-yet"

    return BotResponse(
        reply_text=reply,
        audio_url=fake_audio_url,
        emotion=emotion
    )
