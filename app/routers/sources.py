from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import crud, schemas
from app.auth import get_current_user

router = APIRouter()


#GET открытый — фронтенд и бот читают без авторизации
@router.get("/", response_model=List[schemas.SourceOut], summary="Список RSS-источников")
def list_sources(db: Session = Depends(get_db)):
    return crud.get_sources(db)


#POST, PATCH, DELETE — только для авторизованных администраторов
@router.post("/", response_model=schemas.SourceOut, summary="Добавить RSS-источник", status_code=201)
def create_source(source: schemas.SourceCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return crud.create_source(db, source)


@router.patch("/{source_id}", response_model=schemas.SourceOut, summary="Обновить RSS-источник")
def update_source(source_id: int, data: schemas.SourceUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return crud.update_source(db, source_id, data)


@router.delete("/{source_id}", summary="Удалить RSS-источник")
def delete_source(source_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return crud.delete_source(db, source_id)
