import asyncio
import os
import uuid
import shutil
from dataclasses import dataclass
from typing import Dict, Optional
import subprocess

WORKSPACE_DIR = os.path.join(os.getcwd(), "workspace")
LOGS_DIR = os.path.join(os.getcwd(), "logs")

os.makedirs(WORKSPACE_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

@dataclass
class Job:
    id: str
    process: subprocess.Popen
    log_file: str
    status: str = "running"
    zip_path: Optional[str] = None

jobs: Dict[str, Job] = {}

async def _consume_output(job: Job, project_name: str) -> None:
    assert job.process.stdout
    assert job.process.stdin
    job.process.stdin.write(f"{project_name}\n".encode())
    await job.process.stdin.drain()
    job.process.stdin.close()
    with open(job.log_file, "w") as f:
        async for line in job.process.stdout:
            f.write(line.decode())
    await job.process.wait()
    job.status = "completed" if job.process.returncode == 0 else "error"
    if job.status == "completed":
        zip_base = os.path.join(WORKSPACE_DIR, project_name)
        if os.path.exists(zip_base):
            job.zip_path = shutil.make_archive(zip_base, 'zip', zip_base)

async def start_generation(project_name: str, description: str) -> Job:
    job_id = str(uuid.uuid4())
    process = await asyncio.create_subprocess_exec(
        "python",
        "main.py",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    log_file = os.path.join(LOGS_DIR, f"{job_id}.log")
    job = Job(id=job_id, process=process, log_file=log_file)
    jobs[job_id] = job
    asyncio.create_task(_consume_output(job, project_name))
    return job
