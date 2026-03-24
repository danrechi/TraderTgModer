from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from app import models, schemas


# ── Sources ─────────────────────────────────────────────────────────────────

def get_sources(db: Session):
    return db.query(models.Source).all()

def get_source(db: Session, source_id: int):
    source = db.query(models.Source).filter(models.Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Источник не найден")
    return source

def create_source(db: Session, data: schemas.SourceCreate):
    source = models.Source(name=data.name, url=data.url)
    db.add(source)
    try:
        db.commit()
        db.refresh(source)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Источник с таким URL уже существует")
    return source

def update_source(db: Session, source_id: int, data: schemas.SourceUpdate):
    source = get_source(db, source_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(source, key, value)
    db.commit()
    db.refresh(source)
    return source

def delete_source(db: Session, source_id: int):
    source = get_source(db, source_id)
    db.delete(source)
    db.commit()
    return {"message": "Источник удалён"}


# ── Rules ────────────────────────────────────────────────────────────────────

def get_rules(db: Session):
    return db.query(models.Rule).all()

def get_rule(db: Session, rule_id: int):
    rule = db.query(models.Rule).filter(models.Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Правило не найдено")
    return rule

def create_rule(db: Session, data: schemas.RuleCreate):
    rule = models.Rule(type=data.type, pattern=data.pattern, action=data.action)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule

def delete_rule(db: Session, rule_id: int):
    rule = get_rule(db, rule_id)
    db.delete(rule)
    db.commit()
    return {"message": "Правило удалено"}


# ── News ────────────────────────────────────────────────────────────────────

def get_news(db: Session, limit: int = 100):
    query = db.query(models.NewsItem).order_by(models.NewsItem.fetched_at.desc())
    if limit is not None:
        return query.limit(limit).all()
    return query.all()
