from fastapi import FastAPI
from pydantic import BaseModel
import sys, os

# Ensures Python can locate your modules inside the subdirectory
sys.path.insert(0, "Project - AEGIS")
from aegis import run_pipeline

app = FastAPI(title="Project Aegis")

class Query(BaseModel):
    prompt: str

@app.post("/query")
def query(q: Query):
    return run_pipeline(q.prompt)

@app.get("/")
def health():
    return {"status": "running", "project": "Aegis LLM Gateway"}
