from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.auth import router as auth_router
from app.routes.ideas import router as ideas_router

app = FastAPI(
    title="ProtoX — ProtoIdea API",
    description="AI-powered application idea generator",
    version="1.1.0",
)

# Cookies are only sent to/from these exact origins (allow_credentials=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(ideas_router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": "ProtoX ProtoIdea API"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}