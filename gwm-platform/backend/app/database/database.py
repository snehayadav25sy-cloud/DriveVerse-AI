import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

default_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "database", "gwm.db"))
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"sqlite:///{default_db_path}"
)

# Use connect_args for SQLite fallback if someone runs this locally without docker
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
