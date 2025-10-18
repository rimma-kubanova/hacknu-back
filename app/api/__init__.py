from fastapi import APIRouter
from app.api import user

api_router = APIRouter()
api_router.include_router(user.router, prefix="", tags=["Authentication"])