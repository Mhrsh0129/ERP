"""
database.py — Manages the MySQL database connection using SQLAlchemy.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
# Step 1-> first we locate the current file
# Step 2-> we join the env file with the current file
_here = os.path.dirname(os.path.abspath(__file__)) # Step -> 1
# os.path.dirname -> this removes the file name and keeps only forlder
# os.path.abspath -> this gives the absolute path of the file
# __file__ -> function that return the name of the file
_env = os.path.join(_here, "..", "..", ".env") # Step -> 2
# os.path.join -> this joins the paths
# os.path.exists -> this checks if the file exists
load_dotenv(dotenv_path=_env if os.path.exists(_env) else None, override=True)
# load_dotenv -> enite job is to open a file and reads the valiables inside and load them into python temporary memory
# dotenv_path=_env if os.path.exists(_env) else None -> This is asking the computer a very safe question: "Does the .env file actually exist at the address we just built?"
# override=True -> It ensures your app strictly uses the settings from your .env file, avoiding conflicts.

# Build MySQL Connection URL
DB_USER = os.getenv("DB_USER", "2RsUE3FehSmWPK2.root").strip() # .strip() -> This is a simple string method that removes any accidental spaces, tabs, or newlines from the beginning or end of the text.
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "gateway01.ap-southeast-1.prod.aws.tidbcloud.com").strip()
DB_PORT = os.getenv("DB_PORT", "4000")
DB_NAME = os.getenv("DB_NAME", "test").strip()

# Backward compatible db config for dashboard debug routes
db_config = {
    "user": DB_USER,
    "password": DB_PASSWORD,
    "host": DB_HOST,
    "port": int(DB_PORT),
    "database": DB_NAME
}

DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_size=5, # this tells the app to keep 5 connections open
    max_overflow=10, # this tells the app to open 10 more connections if needed
    pool_recycle=3600 # this tells the app to recycle connections every 3600 seconds
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()

def get_db_connection():
    """
    Returns a raw MySQL connection from the SQLAlchemy connection pool.
    This allows existing models that use raw SQL and cursors to continue working
    while the app gradually migrates to SQLAlchemy.
    """
    return engine.raw_connection()


def test_connection():
    """
    Test the database connection using the SQLAlchemy engine.
    Returns True if successful, False otherwise.
    """
    try:
        with engine.connect() as conn:
            return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False

