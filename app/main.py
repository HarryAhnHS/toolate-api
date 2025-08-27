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
async def log_response(request, call_next):
    resp = await call_next(request)

    body = b""
    async for chunk in resp.body_iterator:
        body += chunk
    # log it
    print("📡 API Response:\n", body.decode(errors="ignore"))
    # re-create the response so client still gets it
    from starlette.responses import Response
    return Response(content=body, status_code=resp.status_code, headers=dict(resp.headers), media_type=resp.media_type)


app.include_router(query.router, prefix="/api")
app.include_router(analyze.router, prefix="/api")
