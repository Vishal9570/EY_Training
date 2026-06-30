from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import create_tables
from app.routes.auth import router as auth_router
from app.routes.planner import router as planner_router

create_tables()
app = FastAPI(title="AI Day Planner API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth_router)
app.include_router(planner_router)


@app.get("/")
def root():
    return {"message": "AI Day Planner API is running", "docs": "http://127.0.0.1:8000/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
