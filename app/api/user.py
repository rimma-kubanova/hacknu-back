from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth import register, login, get_current_user
from app.models import User, UserLogin, UserRegister
from app.database import get_db

router = APIRouter()


@router.post("/register")
def register_user(user: UserRegister, db: Session = Depends(get_db)):
    return register(user, db)

@router.post("/token")
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return login(form_data, db)

@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email}

@router.post("/logout")
def logout_user(user: User = Depends(get_current_user)):
    return {"message": "Logged out"}