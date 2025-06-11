from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from typing import AsyncGenerator
import asyncio
import os
from .models import AnalyzeRequest, AnalysisResponse, GenerateRequest, GenerateResponse, StatusResponse
from .utils import start_generation, jobs, LOGS_DIR

app = FastAPI(title="DevCraft AI API")

@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(req: AnalyzeRequest) -> AnalysisResponse:
    desc = req.description.lower()
    project_type = "generic"
    suggestions = []
    if "chat" in desc:
        project_type = "realtime-chat"
        suggestions.append("socket.io")
    if "ecommerce" in desc:
        project_type = "ecommerce-stripe"
        suggestions.append("stripe integration")
    if "fishing" in desc:
        project_type = "fishing-platform"
        suggestions.append("geolocation")
    if "blog" in desc:
        project_type = "blog-seo"
        suggestions.append("seo optimization")
    return AnalysisResponse(project_type=project_type, suggestions=suggestions)

@app.post("/api/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest) -> GenerateResponse:
    job = await start_generation(req.project_name, req.description)
    return GenerateResponse(job_id=job.id)

@app.get("/api/status/{job_id}", response_model=StatusResponse)
async def status(job_id: str) -> StatusResponse:
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return StatusResponse(job_id=job.id, status=job.status)

@app.get("/api/logs/{job_id}")
async def logs(job_id: str) -> StreamingResponse:
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    log_path = job.log_file
    async def log_stream() -> AsyncGenerator[bytes, None]:
        last = 0
        while True:
            if os.path.exists(log_path):
                with open(log_path, "rb") as f:
                    f.seek(last)
                    chunk = f.read()
                    if chunk:
                        last = f.tell()
                        yield chunk
            if job.status in ("completed", "error"):
                break
            await asyncio.sleep(1)
    return StreamingResponse(log_stream(), media_type="text/plain")

@app.get("/api/download/{job_id}")
async def download(job_id: str) -> FileResponse:
    job = jobs.get(job_id)
    if not job or job.status != "completed" or not job.zip_path:
        raise HTTPException(status_code=400, detail="Job not completed")
    return FileResponse(job.zip_path, filename=os.path.basename(job.zip_path))
