from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime


# ── Source ──────────────────────────────────────────────────────────────────

class SourceCreate(BaseModel):
    name: str
    url: str

class SourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    is_active: Optional[bool] = None

class SourceOut(BaseModel):
    id: int
    name: str
    url: str
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Rule ────────────────────────────────────────────────────────────────────

RuleType = Literal["keyword", "regex", "link"]

class RuleCreate(BaseModel):
    type: RuleType
    pattern: str
    action: Literal["delete", "warn", "ban"] = "delete"

class RuleOut(BaseModel):
    id: int
    type: str
    pattern: str
    action: str
    created_at: datetime
    model_config = {"from_attributes": True}


# ── News ────────────────────────────────────────────────────────────────────

class NewsItemOut(BaseModel):
    id: int
    title: str
    url: str
    source_name: Optional[str] = None
    published_at: Optional[str] = None
    fetched_at: datetime
    model_config = {"from_attributes": True}


# ── Auth ─────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    created_at: datetime
    model_config = {"from_attributes": True}

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
