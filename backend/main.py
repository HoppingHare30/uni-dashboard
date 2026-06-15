import os
from dotenv import load_dotenv

# Load environment variables from backend/.env relative to this file
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(dotenv_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base, SessionLocal
from .routers import auth, library, cafeteria, events, academics, profile, ai
from .routers.academics import seed_academics

# Create database tables
Base.metadata.create_all(bind=engine)

# Seed database with mock PDF data
db = SessionLocal()
try:
    seed_academics(db)
finally:
    db.close()

app = FastAPI(
    title="Unified Campus Intelligence Dashboard API",
    description="Backend API serving 4 MCP mock servers, User Profile database, and Gemini LLM Assistant",
    version="1.0"
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(library.router)
app.include_router(cafeteria.router)
app.include_router(events.router)
app.include_router(academics.router)
app.include_router(profile.router)
app.include_router(ai.router)

@app.get("/")
def read_root():
    return {"message": "Unified Campus Intelligence Dashboard API is online"}
