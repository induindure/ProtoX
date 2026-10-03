from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.preview import router

app = FastAPI(title="Preview API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",  # ProtoCode frontend
        "http://localhost:5175",  # ProtoTest frontend
        "http://localhost:5176",  # Preview frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)
