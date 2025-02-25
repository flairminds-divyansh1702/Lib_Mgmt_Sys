import os
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
from dotenv import load_dotenv

load_dotenv()

# Set up logging
log_level = logging.getLevelName(os.getenv("LOG_LEVEL", "INFO"))
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")

# Create SQLite engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Database connection check
def verify_db_connection():
    try:
        with engine.connect() as connection:
            logger.info("Database connection established successfully!")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")

# Dependency for database session
def get_db():
    db = None
    try:
        db = SessionLocal()
        logger.info("New database session started")
        yield db
    except Exception as e:
        logger.error(f"Error during database session: {e}")
    finally:
        if db:
            db.close()
            logger.info("Database session closed")