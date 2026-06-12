from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.careers.router import router as careers_router
from app.live_match.router import router as live_match_router
from app.season.router import router as season_router

app = FastAPI(title="Cricket Sim API", version="0.1.0")

# Dev-friendly CORS: the Expo dev server runs on a random LAN/localhost port.
# Tighten this to specific origins before shipping a production build.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(careers_router)
app.include_router(live_match_router)
app.include_router(season_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
