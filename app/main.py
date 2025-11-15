from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import confidence, assets, polymarket

app = FastAPI(title="Market Confidence Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten for production if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"ok": True}


app.include_router(confidence.router)
app.include_router(assets.router)
app.include_router(polymarket.router)
