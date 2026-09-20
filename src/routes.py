from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from src.auth import verify_api_key
from src.dependencies import get_db
from src.schemas import CategoryResponse, ProductResponse, SupplierPublicResponse
from src.sql_connect import NorthwindDatabase

public_router = APIRouter()
protected_router = APIRouter(dependencies=[Depends(verify_api_key)])


@public_router.get("/api/v1/products", response_model=list[ProductResponse], tags=["Products"])
def read_products(
    name: str | None = Query(default=None, description="Filter by partial product name"),
    limit: int = Query(default=10, ge=1, le=100),
    db: NorthwindDatabase = Depends(get_db),
) -> list[ProductResponse]:
    try:
        return db.get_products(limit=limit, name=name)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err)
        ) from val_err


@public_router.get(
    "/api/v1/products/{product_id}", response_model=ProductResponse, tags=["Products"]
)
def read_product_by_id(
    product_id: int = Path(..., gt=0),
    db: NorthwindDatabase = Depends(get_db),
) -> ProductResponse:
    product = db.get_product_by_id(product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Product '{product_id}' not found."
        )
    return product


@public_router.get(
    "/api/v1/categories/{category_id}", response_model=CategoryResponse, tags=["Categories"]
)
def read_category_by_id(
    category_id: int = Path(..., gt=0),
    db: NorthwindDatabase = Depends(get_db),
) -> CategoryResponse:
    category = db.get_category_by_id(category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Category '{category_id}' not found."
        )
    return category


@public_router.get(
    "/api/v1/suppliers", response_model=list[SupplierPublicResponse], tags=["Suppliers"]
)
def read_suppliers(
    limit: int = Query(default=10, ge=1, le=30),
    db: NorthwindDatabase = Depends(get_db),
) -> list[SupplierPublicResponse]:
    try:
        return db.get_suppliers(limit=limit)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err)
        ) from val_err


@protected_router.get("/api/v1/table/{table_name}", tags=["Data Access"])
def read_table_data(
    table_name: str,
    id: int | None = Query(default=None, description="Filter by primary key"),
    name: str | None = Query(default=None, description="Filter by partial name match"),
    limit: int = Query(default=10, ge=1, le=100),
    db: NorthwindDatabase = Depends(get_db),
) -> list[dict]:
    try:
        return db.get_table_data(table_name=table_name, limit=limit, record_id=id, name=name)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err)
        ) from val_err


router = APIRouter()
router.include_router(public_router)
router.include_router(protected_router)
