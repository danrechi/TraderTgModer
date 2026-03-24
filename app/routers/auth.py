from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth

router = APIRouter()


@router.post("/register", response_model=schemas.UserOut, status_code=201, summary="Регистрация администратора")
def register(data: schemas.UserCreate, db: Session = Depends(get_db)):
    """Создаёт нового администратора. Логин должен быть уникальным."""
    existing = db.query(models.User).filter(models.User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")

    user = models.User(
        username=data.username,
        hashed_password=auth.get_password_hash(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.Token, summary="Вход в систему (получение JWT)")
def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    """
    Принимает логин и пароль, возвращает JWT-токен.
    Токен нужно передавать в заголовке: Authorization: Bearer <token>
    """
    user = db.query(models.User).filter(models.User.username == data.username).first()
    if not user or not auth.verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}
