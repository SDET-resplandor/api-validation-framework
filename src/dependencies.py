from typing import Generator, Optional
from fastapi import HTTPException, status
from src.sql_conect import NorthwindDatabase
 
db_instance: Optional[NorthwindDatabase] = None
 
def init_db() -> None:
    global db_instance
    db_instance = NorthwindDatabase()
 
def close_db() -> None:
    global db_instance
    db_instance = None
 
def get_db() -> Generator[NorthwindDatabase, None, None]:
    if db_instance is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable."
        )
    yield db_instance
 
def ping_db() -> bool:
    if db_instance is None:
        raise RuntimeError("Database not initialized.")
    return db_instance.ping()
 