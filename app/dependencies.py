from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session
from app.database import get_db
from app.core import security
from app.schemas.token import TokenData
from app.models.user import User as UserModel

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1.2/token")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = security.decode_access_token(token)
    print("Decoded Payload: ", payload)
    user_id: int | None = payload.get("user_id")
    if user_id is None:
        raise credentials_exception
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    print("User Details: ", user)
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    print(current_user)
    return current_user

def get_current_admin_user(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    print("Entered Current Admin User")
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user