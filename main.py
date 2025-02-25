from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.database import engine, Base, get_db, verify_db_connection
from app.models import Books, User
from app.routes.books import router as books_router
from app.routes.user import router as users_router
from app.routes.borrowing import router as borrowing_router
from app.routes.auth import router as auth_router
import logging
from dotenv import load_dotenv

load_dotenv()

# Set up logging
log_level = logging.getLevelName("INFO")
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Library Management System",
    description="A simple library management system API",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully!")
        # Verify database connection
        verify_db_connection()
    except Exception as e:
        logger.error(f"Error during startup: {e}")

# Health check endpoint
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # Try to execute a simple query
        result = db.execute("SELECT 1").scalar()
        return {
            "status": "healthy",
            "database": "connected",
            "test_query_result": result
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

# Include routers
app.include_router(auth_router, prefix="/api/value")
app.include_router(books_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(borrowing_router,prefix="/api/v1.1")

@app.get("/")
async def root():
    return {"message": "Welcome to Library Management System API"}