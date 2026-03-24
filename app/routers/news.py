from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import crud, schemas

router = APIRouter()


#получить все новости из БД
@router.get("/", response_model=List[schemas.NewsItemOut], summary="Список новостей")
def list_news(db: Session = Depends(get_db)):
    #заглушка здесь будет парсинг RSS
    return crud.get_news(db)
