from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import catalog, elements

app = FastAPI(title="Facade Studio")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(catalog.router)
app.include_router(elements.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
