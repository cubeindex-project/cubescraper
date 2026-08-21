from datetime import datetime
from typing import Any

from fastapi import FastAPI

from cubescraper.cube_info_scraper.router import router as cube_info_router
from cubescraper.price_tracker.router import router as price_router

app = FastAPI(
    title="CubeScraper API",
    version="2.0.0",
)

app.include_router(
    cube_info_router,
    prefix="/cube-details",
    tags=["Cube details"],
)

app.include_router(
    price_router,
    prefix="/vendor-offer",
    tags=["Vendor offer"],
)


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "healthy", "timestamp": datetime.now().timestamp()}
