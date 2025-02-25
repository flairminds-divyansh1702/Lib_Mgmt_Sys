from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.models.user import User as UserModel
from app.schemas.user import UserCreate, User as UserSchema
from app.schemas.token import Token, TokenData as TokenSchema
from app.core import security
from app.core.security import get_password_hash

router = APIRouter()

def authenticate_user(db: Session, email: str, password: str):
    """
    Authenticate the user by email and password.
    Returns the user if credentials are valid, or None otherwise.
    """
    user = db.query(UserModel).filter(UserModel.email == email).first()
    print(get_password_hash(password), '||', user.hashed_password)
    print('User Email is:', user.hashed_password,password)
    if not user:
        return None
    if not security.verify_password(password, user.hashed_password):
        return None
    return user

@router.post("/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """
    Generate a JWT token for valid user credentials.
    OAuth2PasswordRequestForm uses the "username" field for the email.
    """
    try:
        user = authenticate_user(db, form_data.username, form_data.password)

        if not user:
            
            return ({
                'response' : 'Incorrect user credential'
                })
        
        access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            data={"user_id": user.id, "is_admin": user.is_admin},
            expires_delta=access_token_expires,
        )
        return {"access_token":access_token, "token_type":"bearer"}

    except Exception as e:
        return ({
            'error': str(e),
            'error_type': str(type(e).__name__),
            'error_file_details': f'error on line {e.__traceback__.tb_lineno} inside {__file__}'
        })

@router.post("/signup", response_model=UserSchema)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    """
    Endpoint for user self-registration.
    This endpoint creates a new user with a hashed password.
    """
    # Check if the email is already registered
    existing_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash the password using the security module
    hashed_password = security.get_password_hash(user.password)
    new_user = UserModel(
        name=user.name,
        email=user.email,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=False  # Default to non-admin
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/signup_with_token", response_model=Token, tags=["Authentication"])
def signup_with_token(user: UserCreate, db: Session = Depends(get_db)):
    """
    Self-registration endpoint that creates a user and immediately returns a JWT token.
    """
    # Check if the email is already registered
    existing_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash the password and create the new user
    hashed_password = security.get_password_hash(user.password)
    new_user = UserModel(
        name=user.name,
        email=user.email,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=False
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create a token for the new user
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"user_id": new_user.id, "is_admin": new_user.is_admin},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}