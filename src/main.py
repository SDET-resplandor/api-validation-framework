from fastapi import FastAPI, HTTPException, Query
from src.sql_conect import NorthwindDatabase

# Inicialización de la app FastAPI
app = FastAPI(
    title="Northwind Data API",
    description="API REST profesional para consulta segura de datos en la base Northwind.",
    version="1.0.0",
)

# Instancia global del repositorio de base de datos
db = NorthwindDatabase()


@app.get("/", tags=["Health"])
def health_check() -> dict:
    """Endpoint de salud para verificar que el servicio esté online."""
    return {"status": "ok", "message": "API Northwind activa y lista."}


@app.get("/api/v1/table/{table_name}", tags=["Data Access"])
def read_table_data(
    table_name: str,
    limit: int = Query(default=10, ge=1, le=100, description="Límite de registros a retornar (1-100)")
) -> list[dict]:
    """
    Obtiene registros de una tabla específica con límite de resultados.
    
    - **table_name**: Nombre exacto de la tabla.
    - **limit**: Número de filas a consultar (por defecto 10, máximo 100).
    """
    try:
        data = db.get_table_data(table_name=table_name, limit=limit)
        return data
    except ValueError as val_err:
        # Error de validación (por ejemplo, nombre de tabla no válido)
        raise HTTPException(status_code=400, detail=str(val_err))
    except RuntimeError as run_err:
        # Error interno en la consulta SQL
        raise HTTPException(status_code=500, detail=str(run_err))


@app.get("/api/v1/customers/{customer_id}", tags=["Customers"])
def read_customer_by_id(customer_id: str) -> dict:
    """
    Busca un cliente específico por su ID único.
    
    - **customer_id**: Identificador del cliente (ejemplo: 'ALFKI').
    """
    try:
        customer = db.get_customer_by_id(customer_id=customer_id)
        if not customer:
            raise HTTPException(
                status_code=404, 
                detail=f"Cliente con ID '{customer_id}' no encontrado."
            )
        return customer
    except RuntimeError as run_err:
        raise HTTPException(status_code=500, detail=str(run_err))