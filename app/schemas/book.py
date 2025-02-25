from pydantic import BaseModel, constr
from datetime import datetime
from typing import Optional

class BookBase(BaseModel):
    title: str
    author: str
    quantity: int = 1

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    quantity: Optional[int] = None

class Book(BookBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True