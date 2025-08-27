# models.py
from pydantic import BaseModel
from typing import Optional

class Project(BaseModel):
    id: int = None
    icon: Optional[str] = None
    type: str
    name: str
    link: str
    theme: str
    is_premium: bool = False
    likes: int = 0
    subscribers: int = 0

class User(BaseModel):
    id: int
    username: Optional[str] = None
    stars: int = 0
    balance: float = 0
    projects_count: int = 0

    class Config:
        json_encoders = {type(None): lambda _: None}