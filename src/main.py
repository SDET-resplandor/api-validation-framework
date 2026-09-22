import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from src.auth import get_expected_api_key
from src.routes import router
from src.sql_connect import NorthwindDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("northwind_api")

tags_metadata = [
    {"name": "Status", "description": "Operational status checks."},
    {"name": "Categories", "description": "Public category lookups."},
    {
        "name": "Products",
        "description": "Public product catalog, enriched with category and supplier name.",
    },
    {
        "name": "Suppliers",
        "description": "Public supplier directory. Only name and ID are exposed.",
    },
    {
        "name": "Data Access",
        "description": "Authenticated access to internal tables via X-API-Key.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_expected_api_key()
    try:
        app.state.db = NorthwindDatabase()
    except FileNotFoundError as fnf_err:
        logger.critical(f"Database file validation failed on startup: {fnf_err}")
        raise
    yield
    app.state.db = None


app = FastAPI(
    title="Northwind API",
    description="""
Public: /api/v1/categories/{id}, /api/v1/products, /api/v1/products/{id}, /api/v1/suppliers.
 
Requires X-API-Key: /api/v1/table/{table_name}, with optional ?id= and ?name= filters.
    """,
    version="2.0.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

app.include_router(router)


# Centralized handler for unexpected DB failures: logs the real error
# server-side, returns a generic message to the client
@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError) -> JSONResponse:
    logger.error(f"Unhandled database error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


@app.get("/", tags=["Status"])
def status_check(request: Request) -> dict:
    db = getattr(request.app.state, "db", None)
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable.",
        )
    try:
        db.ping()
    except RuntimeError as run_err:
        logger.error(f"Health check failed: {run_err}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable.",
        ) from run_err
    return {"status": "ok", "Message": "The Northwind API works"}
