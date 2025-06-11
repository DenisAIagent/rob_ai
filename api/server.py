from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, FileResponse
from typing import AsyncGenerator, Dict
import asyncio
import os
from .models import AnalyzeRequest, AnalysisResponse, GenerateRequest, GenerateResponse, StatusResponse
from .utils import start_generation, jobs, LOGS_DIR

app = FastAPI(title="DevCraft AI API")

analytics: Dict[str, Dict[str, int] | int] = {
    "projects_created": 0,
    "types": {}
}

def record_project(project_type: str) -> None:
    analytics["projects_created"] += 1
    types: Dict[str, int] = analytics["types"]  # type: ignore[assignment]
    types[project_type] = types.get(project_type, 0) + 1

def _detect_type(desc: str) -> tuple[str, list[str]]:
    desc = desc.lower()
    project_type = "generic"
    suggestions: list[str] = []
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
    return project_type, suggestions

@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(req: AnalyzeRequest) -> AnalysisResponse:
    project_type, suggestions = _detect_type(req.description)
    return AnalysisResponse(project_type=project_type, suggestions=suggestions)

@app.post("/api/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest) -> GenerateResponse:
    project_type, _ = _detect_type(req.description)
    record_project(project_type)
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


@app.get("/api/analytics")
async def get_analytics() -> Dict[str, Dict[str, int] | int]:
    return analytics


@app.websocket("/ws/logs/{job_id}")
async def ws_logs(websocket: WebSocket, job_id: str) -> None:
    await websocket.accept()
    job = jobs.get(job_id)
    if not job:
        await websocket.close(code=1008)
        return
    log_path = job.log_file
    last = 0
    try:
        while True:
            if os.path.exists(log_path):
                with open(log_path, "rb") as f:
                    f.seek(last)
                    chunk = f.read()
                    if chunk:
                        last = f.tell()
                        await websocket.send_text(chunk.decode())
            if job.status in ("completed", "error"):
                break
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
    finally:
        await websocket.close()
