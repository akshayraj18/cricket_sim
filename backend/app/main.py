from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.careers.router import router as careers_router
from app.live_match.router import router as live_match_router
from app.season.router import router as season_router

app = FastAPI(title="Cricket Sim API", version="0.1.0")

app.include_router(auth_router)
app.include_router(careers_router)
app.include_router(live_match_router)
app.include_router(season_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
