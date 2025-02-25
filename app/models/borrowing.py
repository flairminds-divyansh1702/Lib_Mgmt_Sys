from datetime import date, datetime, timedelta
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class Borrowing(Base):
    __tablename__ = "borrowings"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    member_id = Column(Integer, ForeignKey("users.id"))
    borrow_date = Column(DateTime, default=datetime.now)
    due_date = Column(DateTime, default=lambda: datetime.now() + timedelta(days=14))
    return_date = Column(DateTime, nullable=True)
    extended = Column(Boolean, default=False)
    
    # Relationships
    book = relationship("Books", back_populates="borrowings")
    member = relationship("User", back_populates="borrowings")