from pydantic import BaseModel, constr, Field
from datetime import datetime
from typing import Optional
from ..schemas.book import Book as BookSchema
from ..schemas.user import User as UserSchema

class BorrowingBase(BaseModel):
    book_id: int
    member_id: int


class BorrowingCreate(BorrowingBase):
    pass


class BorrowingExtend(BaseModel):
    days: int = Field(default=7, gt=0, le=30)


class Borrowing(BorrowingBase):
    id: int
    borrow_date: datetime
    due_date: datetime
    return_date: Optional[datetime] = None
    extended: bool = False

    class Config:
        orm_mode = True


class BorrowingDetail(Borrowing):
    book: BookSchema
    member: UserSchema