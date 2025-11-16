# src/index.py
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routes.confidence_routes import router as confidence_router
from src.routes.asset_routes import router as asset_router
from src.routes.polymarket_routes import router as polymarket_router


app = FastAPI(
    title="Market Confidence Meter API",
    version="0.1.0",
    description="Backend for Market Confidence Meter hackathon project.",
)

# CORS: allow local frontend / anything (hackathon-friendly).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(confidence_router)
app.include_router(asset_router)
app.include_router(polymarket_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# HOW TO RUN (from project root):
#   uvicorn src.index:app --reload
#
# Then open:
#   http://127.0.0.1:8000/docs  for Swagger UI
#   http://127.0.0.1:8000/confidence/overall  etc.
