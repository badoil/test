from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .planner import simple_planner
from .dag_runner import run_plan

app = FastAPI()

class ChatRequest(BaseModel):
    user_id: str | None = None
    text: str

class ChatResponse(BaseModel):
    plan_id: str
    results: dict

@app.post(/chat, response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.text:
        raise HTTPException(status_code=400, detail=text
