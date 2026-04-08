
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

_here = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(_here, "..", "data", "inventory.db")
Database_URL = f"sqlite:///{DB_FILE}"

engine = create_engine(
    Database_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
