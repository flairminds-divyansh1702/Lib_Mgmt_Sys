from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.book import Books
from ..schemas.book import BookCreate, BookUpdate, Book as BookSchema
from ..schemas.borrowing import Borrowing

router = APIRouter()

@router.post("/books", response_model=BookSchema, status_code=status.HTTP_201_CREATED)
def create_book(book: BookCreate, db: Session = Depends(get_db)):
    # Check if book with same title exists
    db_book = db.query(Books).filter(Books.title == Books.title).first()
    if db_book:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Book with this title already exists"
        )
    
    # Create new book
    db_book = Books(**book.model_dump())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

@router.get("/books", response_model=List[BookSchema])
def read_books(
    book_id: Optional[int] = None,
    title: Optional[str] = None,
    author: Optional[str] = None,
    genre: Optional[str] = None,
    available_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    if book_id is not None:
        # Fetch a specific book
        book = db.query(Books).filter(Books.id == book_id).first()
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        # Return as a list for consistent response_model
        return [book]
    if title:
        book = db.query(Books).filter(Books.title.ilike(f"%{title}%"))
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        return [book]
    if author:
        book = db.query(Books).filter(Books.author.ilike(f"%{author}%"))
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        return [book]
    if genre:
        book = db.query(Books).filter(Books.genre.ilike(f"%{genre}%"))
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        return [book]
    if available_only:
        book = db.query(Books).filter(Books.copies_available > 0)
        if not book > 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not available"
            )
        return [book]
    else:
        # Fetch all books with pagination
        books = db.query(Books).offset(skip).limit(limit).all()
        return books

@router.put("/books/{book_id}", response_model=BookSchema)
def update_book(book_id: int, book: BookUpdate, db: Session = Depends(get_db)):
    db_book = db.query(Books).filter(Books.id == book_id).first()
    if db_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    update_data = book.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_book, field, value)
    
    db.commit()
    db.refresh(db_book)
    return db_book

@router.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    db_book = db.query(Books).filter(Books.id == book_id).first()
    if db_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Check if book is currently borrowed
    active_borrowings = db.query(Borrowing).filter(
        Borrowing.book_id == book_id,
        Borrowing.return_date.is_(None)
    ).first()
    
    if active_borrowings:
        raise HTTPException(status_code=400, detail="Cannot delete book that is currently borrowed")
    
    db.delete(db_book)
    db.commit()
    return None