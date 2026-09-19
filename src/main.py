import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from src.auth import get_expected_api_key
from src.dependencies import init_db, close_db, ping_db
from src.routes import router
 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("northwind_api")
 
tags_metadata = [
    {"name": "Status", "description": "Operational status checks."},
    {"name": "Data Access", "description": "Generic relational table access."},
    {"name": "Categories", "description": "Product category management."},
    {"name": "Suppliers", "description": "Supplier directory queries."},
    {"name": "Products", "description": "Product entity lookups."},
]
 
@asynccontextmanager
async def lifespan(app: FastAPI):
    get_expected_api_key()
    try:
        init_db()
    except FileNotFoundError as fnf_err:
        logger.critical(f"Database file validation failed on startup: {fnf_err}")
        raise
    yield
    close_db()
 
app = FastAPI(
    title="Northwind API",
    description="""
 
DATABASE QUERY
 
Requires an X-API-Key header. Refer to README.md for local key setup.
 
    """,
    version="1.0.1",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)
 
app.include_router(router)
 
@app.get("/", tags=["Status"])
def status_check() -> dict:
    try:
        ping_db()
    except RuntimeError as run_err:
        logger.error(f"Health check failed: {run_err}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable.")
    return {"status": "ok", "Message": "The Northwind API works"}
 