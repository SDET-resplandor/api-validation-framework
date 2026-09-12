import sqlite3
from pathlib import Path

# Ruta dinámica al archivo Northwind.db
DB_PATH = Path(__file__).resolve().parent.parent / "data_file" / "Northwind.db"


class NorthwindDatabase:
    """Maneja la conexión y las consultas a la base de datos de forma segura."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._validate_db_exists()

    def _validate_db_exists(self) -> None:
        """Verifica que la base de datos exista antes de intentar conectarse."""
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Error crítico: No se encontró la base de datos en '{self.db_path}'"
            )

    def get_connection(self) -> sqlite3.Connection:
        """Retorna una conexión activa configurada para devolver diccionarios."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_table_data(self, table_name: str, limit: int = 10) -> list[dict]:
        """Obtiene registros de una tabla con límite parametrizado (previene SQLi)."""
        # 1. Seguridad en la estructura: Validamos que el nombre de la tabla sea un identificador SQL válido
        if not table_name.isidentifier():
            raise ValueError(
                f"El nombre de la tabla '{table_name}' no es válido."
            )

        # 2. Uso del comodín '?' para parametrizar el límite de registros
        query = f"SELECT * FROM {table_name} LIMIT ?;"

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # 3. Pasamos el valor dentro de una tupla en execute() -> (limit,)
                cursor.execute(query, (limit,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except sqlite3.Error as error:
            raise RuntimeError(
                f"Error al ejecutar la consulta en '{table_name}': {error}"
            )

    def get_customer_by_id(self, customer_id: str) -> dict | None:
        """Ejemplo práctico de consulta con filtro WHERE completamente parametrizada."""
        # Consulta segura usando '?' para el filtro por ID
        query = "SELECT * FROM Customers WHERE CustomerID = ?;"

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # El id se pasa en la tupla, SQLite desinfecta el valor automáticamente
                cursor.execute(query, (customer_id,))
                row = cursor.fetchone()
                return dict(row) if row else None

        except sqlite3.Error as error:
            raise RuntimeError(
                f"Error al buscar el cliente '{customer_id}': {error}"
            )


# --- Bloque de prueba rápida en terminal ---
if __name__ == "__main__":
    db = NorthwindDatabase()

    print("--- 1. Prueba de tabla completa con límite ---")
    clientes = db.get_table_data("Customers", limit=2)
    print(clientes)

    print("\n--- 2. Prueba de filtro WHERE parametrizado ---")
    cliente_especifico = db.get_customer_by_id("ALFKI")
    print(cliente_especifico)