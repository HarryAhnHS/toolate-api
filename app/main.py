from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routes import query, analyze 
import os

app = FastAPI()

FRONTEND_URL = (os.getenv("FRONTEND_URL") or "http://localhost:3000").rstrip("/")

print("CORS ALLOWED ORIGIN:", FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_origin_header(request: Request, call_next):
    print("Incoming Origin:", request.headers.get("origin"))
    response = await call_next(request)
    return response

app.include_router(query.router, prefix="/api")
app.include_router(analyze.router, prefix="/api")
