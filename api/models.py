from pydantic import BaseModel
from typing import List, Optional

class AnalyzeRequest(BaseModel):
    description: str

class AnalysisResponse(BaseModel):
    project_type: str
    suggestions: List[str]

class GenerateRequest(BaseModel):
    project_name: str
    description: str

class GenerateResponse(BaseModel):
    job_id: str

class StatusResponse(BaseModel):
    job_id: str
    status: str
