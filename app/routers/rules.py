from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import crud, schemas
from app.auth import get_current_user

router = APIRouter()


#GET открытый
@router.get("/", response_model=List[schemas.RuleOut], summary="Список правил фильтрации")
def list_rules(db: Session = Depends(get_db)):
    return crud.get_rules(db)


#POST и DELETE — только для авторизованных администраторов
@router.post("/", response_model=schemas.RuleOut, summary="Добавить правило фильтрации", status_code=201)
def create_rule(rule: schemas.RuleCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return crud.create_rule(db, rule)


@router.delete("/{rule_id}", summary="Удалить правило фильтрации")
def delete_rule(rule_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return crud.delete_rule(db, rule_id)
