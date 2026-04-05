from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import Base, engine
from app.routes.ideas import router as ideas_router

# Create all tables on startup (Supabase PostgreSQL)
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ProtoX — ProtoIdea API",
    description="AI-powered application idea generator using LangChain + Gemini 1.5 Flash",
    version="1.0.0",
)

# Allow requests from the React frontend (Vite default port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ideas_router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": "ProtoX ProtoIdea API"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
