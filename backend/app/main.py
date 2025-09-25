import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db
from .auth import router as auth_router
from .routers import api as api_router
from .scheduler import start_scheduler

app = FastAPI(title="Time Tracker API")

DOMAIN = os.getenv("DOMAIN", "localhost")
origins = [f"https://app.{DOMAIN}", f"http://app.{DOMAIN}", "http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(api_router)

@app.on_event("startup")
def on_startup():
    init_db()
    try:
        start_scheduler()
    except Exception as e:
        print("Scheduler start error:", e)

@app.get("/health")
def health():
    return {"ok": True}
