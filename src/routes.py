import logging
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from src.sql_conect import NorthwindDatabase
from src.auth import verify_api_key
from src.dependencies import get_db
from src.schemas import CategoryResponse, SupplierResponse, ProductResponse
 
logger = logging.getLogger("northwind_api")
 
router = APIRouter()

@router.get(
    "/api/v1/table/{table_name}",
    tags=["Data Access"],
    dependencies=[Depends(verify_api_key)],
)
def read_table_data(
    table_name: str,
    limit: int = Query(default=10, ge=1, le=100, description="Result limit"),
    db: NorthwindDatabase = Depends(get_db),
) -> list[dict]:
    try:
        return db.get_table_data(table_name=table_name, limit=limit)
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except RuntimeError as run_err:
        logger.error(f"Database error on table '{table_name}': {run_err}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")
 
@router.get("/api/v1/categories/{category_id}", response_model=CategoryResponse, tags=["Categories"])
def read_category_by_id(
    category_id: int = Path(..., gt=0, description="Positive category identifier"),
    db: NorthwindDatabase = Depends(get_db),
) -> CategoryResponse:
    try:
        category = db.get_category_by_id(category_id=category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category '{category_id}' not found.",
            )
        return category
    except RuntimeError as run_err:
        logger.error(f"Error fetching category '{category_id}': {run_err}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error."
        )
 
@router.get("/api/v1/suppliers", response_model=list[SupplierResponse], tags=["Suppliers"])
def read_suppliers(
    limit: int = Query(default=10, ge=1, le=30, description="Result limit"),
    db: NorthwindDatabase = Depends(get_db)
) -> list[SupplierResponse]:
    try:
        return db.get_table_data(table_name="Suppliers", limit=limit)
    except RuntimeError as run_err:
        logger.error(f"Error fetching suppliers: {run_err}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")
 
@router.get("/api/v1/products/{product_id}", response_model=ProductResponse, tags=["Products"])
def read_product_by_id(
    product_id: int = Path(..., gt=0, description="Positive product identifier"),
    db: NorthwindDatabase = Depends(get_db),
) -> ProductResponse:
    try:
        product = db.get_product_by_id(product_id=product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product '{product_id}' not found.",
            )
        return product
    except RuntimeError as run_err:
        logger.error(f"Error fetching product '{product_id}': {run_err}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")