from pydantic import BaseModel, ConfigDict, Field


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    category_id: int = Field(..., alias="CategoryID")
    category_name: str = Field(..., alias="CategoryName")
    description: str | None = Field(None, alias="Description")


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    product_id: int = Field(..., alias="ProductID")
    product_name: str = Field(..., alias="ProductName")
    unit: str | None = Field(None, alias="Unit")
    price: float | None = Field(None, alias="Price")
    category_id: int | None = Field(None, alias="CategoryID")
    category_name: str | None = Field(None, alias="CategoryName")
    supplier_name: str | None = Field(None, alias="SupplierName")


class SupplierPublicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    supplier_id: int = Field(..., alias="SupplierID")
    supplier_name: str = Field(..., alias="SupplierName")
