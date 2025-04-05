from fastapi import FastAPI
from app.routes import query, analyze

app = FastAPI()
app.include_router(query.router, prefix="/api")
app.include_router(analyze.router, prefix="/api")