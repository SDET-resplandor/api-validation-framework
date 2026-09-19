from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
 
class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
 
    category_id: int = Field(..., alias="CategoryID", description="Unique category identifier")
    category_name: str = Field(..., alias="CategoryName", description="Category name")
    description: Optional[str] = Field(None, alias="Description", description="Category description")
 
class SupplierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
 
    supplier_id: int = Field(..., alias="SupplierID", description="Unique supplier identifier")
    supplier_name: str = Field(..., alias="CompanyName", description="Supplier organization name")
 
class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
 
    product_id: int = Field(..., alias="ProductID", description="Unique product identifier")
    product_name: str = Field(..., alias="ProductName", description="Product name")
    supplier_id: Optional[int] = Field(None, alias="SupplierID", description="Associated supplier identifier")
    category_id: Optional[int] = Field(None, alias="CategoryID", description="Associated category identifier")
    quantity_per_unit: Optional[str] = Field(None, alias="QuantityPerUnit", description="Package quantity description")
    unit_price: Optional[float] = Field(None, alias="UnitPrice", description="Price per unit")
    units_in_stock: Optional[int] = Field(None, alias="UnitsInStock", description="Units currently in stock")
    units_on_order: Optional[int] = Field(None, alias="UnitsOnOrder", description="Units currently on order")
    reorder_level: Optional[int] = Field(None, alias="ReorderLevel", description="Stock level that triggers reorder")
    discontinued: Optional[int] = Field(None, alias="Discontinued", description="Discontinued flag")