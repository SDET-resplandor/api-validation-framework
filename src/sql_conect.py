import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data_file" / "Northwind.db"


class NorthwindDatabase:
    """Wraps connection management and secured queries for Northwind SQLite DB."""

    ALLOWED_TABLES: set[str] = {
        "products",
        "categories",
        "suppliers",
    }

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._validate_db_exists()

    def _validate_db_exists(self) -> None:
        if not self.db_path.exists():
            raise FileNotFoundError(f"Couldn't find the database at '{self.db_path}'")

    @contextmanager
    def get_connection(self):
        """Context manager that guarantees the connection is closed after execution."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def get_table_data(self, table_name: str, limit: int = 10) -> list[dict]:
        """Fetches rows from an authorized table, preventing unauthorized data access."""
        clean_table_name = table_name.lower().strip()

        if clean_table_name not in self.ALLOWED_TABLES:
            raise ValueError(f"Access denied: '{table_name}' is not an authorized public table.")

        if limit <= 0:
            raise ValueError("Limit must be a positive integer.")

        query = f"SELECT * FROM {clean_table_name} LIMIT ?;"

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (limit,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as error:
            raise RuntimeError(f"Query failed on '{table_name}': {error}")

    def get_product_by_id(self, products_id: str) -> dict | None:
        """Looks up one Products by ID using a parameterized WHERE clause with NOCASE support."""
        query = "SELECT * FROM Products WHERE ProductID = ? COLLATE NOCASE;"

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (products_id.strip(),))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as error:
            raise RuntimeError(f"Failed to look up Product '{products_id}': {error}")

if __name__ == "__main__":
    db = NorthwindDatabase()

    print(" ----SMOKE TEST---- ")

    products = db.get_table_data("Products", limit=2)
    print(f"[OK] Fetched {len(products)} rows:")
    print(f"     Sample row keys: {list(products[0].keys())}")
    print(f"     Sample data: {products[0]}")

    if product_found := db.get_product_by_id("1"):
        print(f"[OK] Found product: {product_found}")
    else:
        print("[WARNING] Product ID '1' not found.")
        
    try:
        db.get_table_data("Employees")
    except ValueError as err:
        print(f"[OK] Access Denied: {err}")