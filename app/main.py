from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router
from app.core.config import get_settings

app = FastAPI(title="Stock Insights Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

app.mount(
    "/",
    StaticFiles(directory="frontend", html=True),
    name="static",
)


@app.on_event("startup")
def _validate_env_on_startup() -> None:
    # Per spec: fail fast on missing keys (clear error message).
    get_settings()


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}
