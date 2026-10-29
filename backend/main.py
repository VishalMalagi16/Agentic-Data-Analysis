# main.py
import os
import io
import uuid
import pandas as pd
import redis
import redis.asyncio as aredis
import pickle
import asyncio
import json
import time # <-- SOLUTION: Import the time module

from fastapi import FastAPI, UploadFile, File, Request, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from orchestrator import OrchestratorAgent
from analysis_state import AnalysisState

# --- FastAPI App Initialization & Middleware ---
app = FastAPI(title="Agentic Analysis API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# --- Static Files & Redis Clients ---
PLOTS_DIR = os.path.join("artifacts", "plots")
DATASETS_DIR = os.path.join("artifacts", "datasets")
os.makedirs(PLOTS_DIR, exist_ok=True)
os.makedirs(DATASETS_DIR, exist_ok=True)
app.mount("/plots", StaticFiles(directory=PLOTS_DIR), name="plots")
app.mount("/datasets", StaticFiles(directory=DATASETS_DIR), name="datasets")

redis_host = os.environ.get("REDIS_HOST", "localhost")

sync_redis_state_client = redis.Redis(host=redis_host, port=6379, db=0)
sync_redis_pubsub_client = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)
async_redis_client = aredis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)

@app.on_event("startup")
async def startup_event():
    try:
        sync_redis_state_client.ping()
        await async_redis_client.ping()
        print("Successfully connected to Redis with both sync and async clients.")
    except Exception as e:
        print(f"FATAL ERROR: Could not connect to Redis on startup: {e}")

# --- Pydantic Models & Orchestrator ---
class AnalysisRequest(BaseModel):
    session_id: str
    prompt: str
orchestrator = OrchestratorAgent()

# --- SSE Streaming Endpoint ---
@app.get("/session/stream/{session_id}")
async def stream_session(request: Request, session_id: str):
    async def event_generator():
        pubsub = async_redis_client.pubsub()
        channel = f"session-updates:{session_id}"
        ready_key = f"session-ready:{session_id}"
        await pubsub.subscribe(channel)
        await async_redis_client.set(ready_key, "1", ex=20)
        
        try:
            while True:
                if await request.is_disconnected(): break
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    yield message['data']
                    if json.loads(message['data']).get("event") == "end": break
                await asyncio.sleep(0.1)
        finally:
            await pubsub.unsubscribe(channel)
            await async_redis_client.delete(ready_key)
            print(f"Client disconnected. Cleaned up for {session_id}")

    return EventSourceResponse(event_generator())

# --- Background Task Wrapper ---
def run_orchestration_in_thread(session_id, prompt, is_initial_run):
    # SOLUTION: Add a small delay to give the frontend time to connect to the SSE stream.
    time.sleep(0.1)
    
    state_bytes = sync_redis_state_client.get(session_id)
    if not state_bytes:
        print(f"Error: Could not find state for session {session_id}")
        return
    state = pickle.loads(state_bytes)
    orchestrator.run(
        state=state, user_prompt=prompt, session_id=session_id,
        redis_state_client=sync_redis_state_client,
        redis_pubsub_client=sync_redis_pubsub_client,
        is_initial_run=is_initial_run
    )

# --- API Endpoints ---
@app.post("/session/start")
async def start_session(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        session_id = str(uuid.uuid4())
        initial_prompt ="Perform data summary on the dataset. Once you get results perform preprocessing agent . Then do univarite analysis on all the valid columns and bivarite on valid pairs. "
        state = AnalysisState(user_prompt=initial_prompt, df=df)
        
        sync_redis_state_client.set(session_id, pickle.dumps(state), ex=3600)
        session_started_key = f"session-started:{session_id}"
        sync_redis_state_client.set(session_started_key, "1", ex=3600)
        
        background_tasks.add_task(run_orchestration_in_thread, session_id=session_id, prompt=initial_prompt, is_initial_run=True)
        
        return {"session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/session/analyze")
async def analyze_follow_up(request: AnalysisRequest, background_tasks: BackgroundTasks):
    session_started_key = f"session-started:{request.session_id}"
    if not sync_redis_state_client.exists(session_started_key):
        raise HTTPException(status_code=404, detail="Session not found or expired.")
    
    try:
        background_tasks.add_task(run_orchestration_in_thread, session_id=request.session_id, prompt=request.prompt, is_initial_run=False)
        return {"session_id": request.session_id, "message": "Analysis started."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))