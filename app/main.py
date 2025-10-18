from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.api import api_router
from app.api.files import router as files_router
from app.api.generate import router as generate_router

Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="HackNU Dropouts Backend",
    description="AI-powered mockup and content generation API",
    version="1.0.0"
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "HackNU Dropouts Backend API",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "auth": "/register, /token, /me",
            "files": "/files (POST), /files/{id} (GET)",
            "generation": "/api/generate_image, /api/generate_video"
        }
    }

# Include routers
app.include_router(api_router)  # User auth endpoints
app.include_router(files_router)  # File upload/serve
app.include_router(generate_router)  # AI generation endpoints