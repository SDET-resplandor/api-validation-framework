from collections.abc import Generator

from fastapi import HTTPException, Request, status

from src.sql_connect import NorthwindDatabase


def get_db(request: Request) -> Generator[NorthwindDatabase]:
    db = getattr(request.app.state, "db", None)
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable.",
        )
    yield db
