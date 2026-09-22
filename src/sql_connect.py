import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data_file" / "Northwind.db"
CONNECTION_TIMEOUT = 30
# Maps each whitelisted table to its primary key and an optional
# searchable name column, so the generic endpoint can filter safely
# without hardcoding per-table logic.
TABLE_METADATA = {
    "categories": {"pk": "CategoryID", "name_column": "CategoryName"},
    "products": {"pk": "ProductID", "name_column": "ProductName"},
    "suppliers": {"pk": "SupplierID", "name_column": "SupplierName"},
    "employees": {"pk": "EmployeeID", "name_column": "LastName"},
    "shippers": {"pk": "ShipperID", "name_column": "ShipperName"},
    "customers": {"pk": "CustomerID", "name_column": "CustomerName"},
    "orders": {"pk": "OrderID", "name_column": None},
    "orderdetails": {"pk": "OrderDetailID", "name_column": None},
}


class NorthwindDatabase:
    _PRODUCT_QUERY_BASE = """
        SELECT
            p.ProductID AS ProductID,
            p.ProductName AS ProductName,
            p.Unit AS Unit,
            p.Price AS Price,
            p.CategoryID AS CategoryID,
            c.CategoryName AS CategoryName,
            s.SupplierName AS SupplierName
        FROM Products p
        LEFT JOIN Categories c ON p.CategoryID = c.CategoryID
        LEFT JOIN Suppliers s ON p.SupplierID = s.SupplierID
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._validate_db_exists()
        self._enable_wal_mode()

    def _validate_db_exists(self) -> None:
        if not self.db_path.exists():
            raise FileNotFoundError(f"Couldn't find database at '{self.db_path}'")

    def _enable_wal_mode(self) -> None:
        conn = sqlite3.connect(self.db_path, timeout=CONNECTION_TIMEOUT)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
        except sqlite3.Error as error:
            raise RuntimeError(f"Failed to enable WAL mode: {error}") from error
        finally:
            conn.close()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=CONNECTION_TIMEOUT)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def ping(self) -> bool:
        try:
            with self.get_connection() as conn:
                conn.execute("SELECT 1;")
            return True
        except sqlite3.Error as error:
            raise RuntimeError(f"Health check failed: {error}") from error

    @staticmethod
    def _escape_like(value: str) -> str:
        # Escapes SQL LIKE wildcards (% and _) so user input can't turn a
        # name filter into an unintended "match everything" query.
        return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    def get_products(self, limit: int = 10, name: str | None = None) -> list[dict]:
        if limit <= 0:
            raise ValueError("Limit must be positive.")

        clean_name = name.strip() if name else None
        params: list = []
        where_clause = ""
        if clean_name:
            where_clause = "WHERE p.ProductName LIKE ? ESCAPE '\\'"
            params.append(f"%{self._escape_like(clean_name)}%")

        query = f"{self._PRODUCT_QUERY_BASE} {where_clause} LIMIT ?;"
        params.append(limit)
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as error:
            raise RuntimeError(f"Query failed on 'Products': {error}") from error

    def get_product_by_id(self, product_id: int) -> dict | None:
        query = f"{self._PRODUCT_QUERY_BASE} WHERE p.ProductID = ?;"
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (product_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as error:
            raise RuntimeError(f"Failed to fetch product {product_id}: {error}") from error

    def get_category_by_id(self, category_id: int) -> dict | None:
        query = "SELECT * FROM Categories WHERE CategoryID = ?;"
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (category_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as error:
            raise RuntimeError(f"Failed to fetch category {category_id}: {error}") from error

    def get_suppliers(self, limit: int = 10) -> list[dict]:
        if limit <= 0:
            raise ValueError("Limit must be positive.")
        query = "SELECT SupplierID, SupplierName FROM Suppliers LIMIT ?;"
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as error:
            raise RuntimeError(f"Query failed on 'Suppliers': {error}") from error

    def get_table_data(
        self,
        table_name: str,
        limit: int = 10,
        record_id: int | None = None,
        name: str | None = None,
    ) -> list[dict]:
        clean_table_name = table_name.lower().strip()
        metadata = TABLE_METADATA.get(clean_table_name)
        if metadata is None:
            raise ValueError(f"'{table_name}' is not an authorized table.")
        if limit <= 0:
            raise ValueError("Limit must be positive.")

        conditions = []
        params: list = []

        if record_id is not None:
            conditions.append(f"{metadata['pk']} = ?")
            params.append(record_id)

        if name is not None:
            if metadata["name_column"] is None:
                raise ValueError(f"'{table_name}' does not support filtering by name.")
            conditions.append(f"{metadata['name_column']} LIKE ? ESCAPE '\\'")
            params.append(f"%{self._escape_like(name.strip())}%")

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM {clean_table_name} {where_clause} LIMIT ?;"
        params.append(limit)

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as error:
            raise RuntimeError(f"Query failed on '{table_name}': {error}") from error
