from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Union
from ..database import get_db
from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate, User as UserSchema
from ..models.borrowing import Borrowing
from ..core.security import get_password_hash
router = APIRouter()

@router.post("/users", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user with same email exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)  # Hash the password
    new_user = User(
        name=user.name,
        email=user.email,
        hashed_password=hashed_password,  # Store hashed password
        is_active=user.is_active
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/users/{user_id}", response_model=Union[List[UserSchema], UserSchema])
def read_users(
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    if user_id is not None:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.put("/users/{user_id}", response_model=UserSchema)
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if User.email != db_user.email:
        existing_member = db.query(User).filter(User.email == db_user.email).first()
        if existing_member:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    update_data = user.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

@router.put("/users/{user_id}/activate", response_model=UserSchema)
def activate_member(member_id: int, db: Session = Depends(get_db)):
    """Activate a member's account."""
    db_member = db.query(User).filter(User.id == member_id).first()
    if db_member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    
    db_member.is_active = True
    db.commit()
    db.refresh(db_member)
    return db_member


@router.put("/members/{user_id}/deactivate", response_model=UserSchema)
def deactivate_member(member_id: int, db: Session = Depends(get_db)):
    """Deactivate a member's account."""
    db_member = db.query(User).filter(User.id == member_id).first()
    if db_member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Check if member has any active borrowings
    active_borrowings = db.query(Borrowing).filter(
        Borrowing.member_id == member_id,
        Borrowing.return_date.is_(None)
    ).first()
    
    if active_borrowings:
        raise HTTPException(
            status_code=400, 
            detail="Cannot deactivate member with active borrowings"
        )
    
    db_member.is_active = False
    db.commit()
    db.refresh(db_member)
    return db_member

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if member has any borrowing history
    borrowings = db.query(Borrowing).filter(Borrowing.member_id == user_id).first()
    if borrowings:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete member with borrowing history. Consider deactivating instead."
        )
    
    db.delete(db_user)
    db.commit()
    return None