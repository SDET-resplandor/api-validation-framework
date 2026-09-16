import logging
from typing import Generator
from fastapi import Depends, FastAPI, HTTPException, Query
from src.sql_conect import NorthwindDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("northwind_api")

app = FastAPI(
    title="Northwind Data API",
    description="REST API for querying the Northwind database.",
    version="1.0.0",
)

def get_db() -> Generator[NorthwindDatabase, None, None]:
    """Dependency provider for database instance (enables easy test mocking)."""
    try:
        db = NorthwindDatabase()
        yield db
    except FileNotFoundError as fnf_err:
        logger.error(f"Database initialization failed: {fnf_err}")
        raise HTTPException(
            status_code=500, detail="Database resource unavailable."
        )

@app.get("/", tags=["Health"])
def health_check() -> dict:
    """Simple check to confirm the service is up and running."""
    return {"status": "ok", "message": "Northwind API is running."}


@app.get("/api/v1/table/{table_name}", tags=["Data Access"])
def read_table_data(
    table_name: str,
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Max number of rows to return (1-100)",
    ),
    db: NorthwindDatabase = Depends(get_db),
) -> list[dict]:
    """Returns rows from an allowed table, capped by the limit parameter."""
    try:
        return db.get_table_data(table_name=table_name, limit=limit)
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except RuntimeError as run_err:
        logger.error(
            f"Database error on table '{table_name}': {run_err}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error.")

@app.get("/api/v1/products/{product_id}", tags=["Products"])
def read_product_by_id(
    product_id: str,
    db: NorthwindDatabase = Depends(get_db),
) -> dict:
    """Looks up a single product by ID."""
    clean_id = product_id.strip()
    try:
        product = db.get_product_by_id(products_id=clean_id)
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product with ID '{clean_id}' not found.",
            )
        return product
    except RuntimeError as run_err:
        logger.error(
            f"Database error on product lookup '{clean_id}': {run_err}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal server error.")