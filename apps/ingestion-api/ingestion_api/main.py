from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Imbryk Ingestion API", version="0.1.0")


class HealthResponse(BaseModel):
    status: str


class PromptRequest(BaseModel):
    prompt: str
    user_id: str


class PromptResponse(BaseModel):
    id: str
    status: str


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok")


@app.post("/prompts", response_model=PromptResponse)
async def submit_prompt(request: PromptRequest):
    # TODO: Validate payment, queue prompt for processing
    return PromptResponse(id="stub", status="accepted")
