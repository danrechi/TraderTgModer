from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app import models

#секретный ключ — в production хранить в .env
SECRET_KEY = "trader-news-super-secret-key-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 часа

security = HTTPBearer()


def verify_password(plain: str, hashed: str) -> bool:
    """Проверяет пароль против bcrypt-хэша"""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def get_password_hash(password: str) -> str:
    """Хэширует пароль через bcrypt"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создаёт JWT-токен с payload и временем жизни"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    Middleware-зависимость FastAPI.
    Извлекает JWT из заголовка Authorization: Bearer <token>,
    декодирует, находит пользователя в БД.
    Если токен невалиден — возвращает HTTP 401.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Недействительный или просроченный токен",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user
