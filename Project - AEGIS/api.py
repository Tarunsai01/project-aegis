from fastapi import FastAPI
from pydantic import BaseModel
import sys
import os

# Force Python to look in the current directory for aegis.py
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

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
run_pipeline = process
