from fastapi import FastAPI

from app.config import AI_MODE

app = FastAPI(title="CriadorDeMapas")


@app.get("/health")
def health():
    return {"status": "ok", "ai_mode": AI_MODE}
