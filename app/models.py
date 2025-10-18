from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)


class VideoGeneration(Base):
    __tablename__ = "video_generations"

    id = Column(Integer, primary_key=True, index=True)
    video_url = Column(String)
    prompt = Column(String)
    aspect_ratio = Column(String)
    job_set_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserRegister(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str
