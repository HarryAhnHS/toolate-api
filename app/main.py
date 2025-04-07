from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import query, analyze 
import os

app = FastAPI()

FRONTEND_URL = os.getenv("FRONTEND_URL") or "http://localhost:3000"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query.router, prefix="/api")
app.include_router(analyze.router, prefix="/api")
