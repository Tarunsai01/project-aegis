from fastapi import FastAPI
from pydantic import BaseModel
import sys
import os

# Dynamically add the current folder to the path, no matter what it's named
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from aegis import run_pipeline
except ImportError:
    # Fallback in case it's executing from one level up
    sys.path.insert(0, os.path.join(current_dir, "Project - AEGIS"))
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
