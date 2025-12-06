from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from cubescraper.cube_info_scraper.main import process_job

app = FastAPI()


class AutofillRequest(BaseModel):
    id: int
    url: str


@app.post("/autofill")
async def autofill(req: AutofillRequest):
    job_id = req.id
    store_url = req.url.strip()

    if job_id is None or not store_url:
        raise HTTPException(status_code=400, detail="Invalid request")

    try:
        data = await process_job(job_id, store_url)
    except Exception:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    else:
        if not data:
            raise HTTPException(status_code=404, detail="No data found")

    return {"id": job_id, "autofilled": data}
