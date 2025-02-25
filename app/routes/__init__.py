from .books import router as books_router
from .user import router as users_router
from .auth import router as auth_router

__all__ = ['books_router', 'users_router', 'auth_router']