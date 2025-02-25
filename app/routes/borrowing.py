from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Union
from datetime import datetime, timedelta
from ..database import get_db
from ..models.user import User
from ..models.book import Books
from ..models.borrowing import Borrowing
from ..schemas.borrowing import BorrowingCreate, BorrowingDetail, BorrowingExtend, Borrowing as BorrowingSchema
from ..dependencies import get_current_active_user, get_current_admin_user

router = APIRouter()

@router.post("/borrowings/", response_model=BorrowingSchema, status_code=status.HTTP_201_CREATED)
def create_borrowing(borrowing: BorrowingCreate, db: Session = Depends(get_db)):
    """Create a new borrowing record."""
    # Verify book exists and is available
    db_book = db.query(Books).filter(Books.id == borrowing.book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    if db_book.quantity <= 0:
        raise HTTPException(status_code=400, detail="Book is not available for borrowing")

    # Verify member exists and is active
    db_member = db.query(User).filter(User.id == borrowing.member_id).first()
    if db_member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    if not db_member.is_active:
        raise HTTPException(status_code=400, detail="Member account is not active")

    # Create borrowing record
    db_borrowing = Borrowing(**borrowing.dict())
    
    # Update book availability
    db_book.quantity -= 1
    
    db.add(db_borrowing)
    db.commit()
    db.refresh(db_borrowing)
    return db_borrowing

@router.get("/borrowings/", response_model=Union[BorrowingDetail, List[BorrowingSchema]])
def read_borrowings(
    borrowing_id: Optional[int] = None,
    skip: int = 0, 
    limit: int = 100, 
    book_id: Optional[int] = None,
    member_id: Optional[int] = None,
    active_only: bool = False,
    overdue_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get borrowing records.
    - If `borrowing_id` is provided, returns a specific borrowing record including detailed book and user info.
    - Otherwise, returns a list of borrowings with optional filtering and pagination.
    """
    if borrowing_id is not None:
        db_borrowing = db.query(Borrowing).filter(Borrowing.id == borrowing_id).first()
        if not db_borrowing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Borrowing record not found"
            )
        return db_borrowing

    query = db.query(Borrowing)
    
    if book_id is not None:
        query = query.filter(Borrowing.book_id == book_id)
    if member_id is not None:
        query = query.filter(Borrowing.member_id == member_id)
    if active_only:
        query = query.filter(Borrowing.return_date.is_(None))
    if overdue_only:
        query = query.filter(
            Borrowing.return_date.is_(None),
            Borrowing.due_date < datetime.now()
        )
        
    borrowings = query.offset(skip).limit(limit).all()
    return borrowings

@router.put("/borrowings/{borrowing_id}/return", response_model=BorrowingSchema)
def return_book(borrowing_id: int, db: Session = Depends(get_db)):
    """Record the return of a borrowed book."""
    db_borrowing = db.query(Borrowing).filter(Borrowing.id == borrowing_id).first()
    if db_borrowing is None:
        raise HTTPException(status_code=404, detail="Borrowing record not found")
    
    if db_borrowing.return_date is not None:
        raise HTTPException(status_code=400, detail="Book has already been returned")
    
    # Update return date
    db_borrowing.return_date = datetime.now()
    
    # Increase available copies
    db_book = db.query(Books).filter(Books.id == db_borrowing.book_id).first()
    db_book.copies_available += 1
    
    db.commit()
    db.refresh(db_borrowing)
    return db_borrowing

@router.put("/borrowings/{borrowing_id}/extend", response_model=BorrowingSchema)
def extend_borrowing(borrowing_id: int, extension: BorrowingExtend, db: Session = Depends(get_db)):
    """Extend the due date for a borrowed book."""
    db_borrowing = db.query(Borrowing).filter(Borrowing.id == borrowing_id).first()
    if db_borrowing is None:
        raise HTTPException(status_code=404, detail="Borrowing record not found")
    
    if db_borrowing.return_date is not None:
        raise HTTPException(status_code=400, detail="Cannot extend already returned book")
    
    if db_borrowing.extended:
        raise HTTPException(status_code=400, detail="Borrowing period has already been extended once")
    
    # Extend due date
    db_borrowing.due_date = db_borrowing.due_date + timedelta(days=extension.days)
    db_borrowing.extended = True
    
    db.commit()
    db.refresh(db_borrowing)
    return db_borrowing


@router.get("/borrowing/", response_model=List[BorrowingDetail])
def read_all_borrowings(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):  
    print("current user configs",current_user.is_admin, current_user.is_active)
    if current_user.is_admin:
        borrowings = db.query(Borrowing).all()
    else:
        borrowings = db.query(Borrowing).filter(Borrowing.member_id == current_user.id).all()
    return borrowings