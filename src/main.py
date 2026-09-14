import logging
from fastapi import FastAPI, HTTPException, Query
from src.sql_conect import NorthwindDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("northwind_api")

app = FastAPI(
    title="Northwind Data API",
    description="REST API for querying the Northwind database.",
    version="1.0.0",
)

db = NorthwindDatabase()


@app.get("/", tags=["Health"])
def health_check() -> dict:
    """Simple check to confirm the service is up and running."""
    return {"status": "ok", "message": "Northwind API is running."}


@app.get("/api/v1/table/{table_name}", tags=["Data Access"])
def read_table_data(
    table_name: str,
    limit: int = Query(default=10, ge=1, le=100, description="Max number of rows to return (1-100)")
) -> list[dict]:
    """
    Returns rows from the given table, capped by the limit parameter.

    - **table_name**: exact table name.
    - **limit**: how many rows to fetch (default 10, max 100).
    """
    try:
        return db.get_table_data(table_name=table_name, limit=limit)
    except ValueError as val_err:
        
        raise HTTPException(status_code=400, detail=str(val_err))
    except RuntimeError as run_err:
        
        logger.error(f"Database error on table '{table_name}': {run_err}", exc_info=True)
        
        raise HTTPException(status_code=500, detail="Internal server error.")


@app.get("/api/v1/customers/{customer_id}", tags=["Customers"])
def read_customer_by_id(customer_id: str) -> dict:
    """
    Looks up a single customer by ID.

    - **customer_id**: e.g. 'ALFKI'.
    """
    try:
        customer = db.get_customer_by_id(customer_id=customer_id)
        if not customer:
            raise HTTPException(
                status_code=404,
                detail=f"Customer with ID '{customer_id}' not found."
            )
        return customer
    except RuntimeError as run_err:
       
        logger.error(f"Database error on customer lookup '{customer_id}': {run_err}", exc_info=True)
        
        raise HTTPException(status_code=500, detail="Internal server error.")