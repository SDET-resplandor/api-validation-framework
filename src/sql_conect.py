import sqlite3
from contextlib import contextmanager
from pathlib import Path
 
DB_PATH = Path(__file__).resolve().parents[1] / "data_file" / "Northwind.db"
CONNECTION_TIMEOUT = 30
 
class NorthwindDatabase:
    ALLOWED_TABLES: set[str] = {"products","categories","suppliers","employees","shippers","customers","orders","orderdetails",}

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
            raise RuntimeError(f"Failed to enable WAL mode: {error}")
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
            raise RuntimeError(f"Health check failed: {error}")
 
    def get_table_data(self, table_name: str, limit: int = 10) -> list[dict]:
        clean_table_name = table_name.lower().strip()
        if clean_table_name not in self.ALLOWED_TABLES:
            raise ValueError(f"Access denied: '{table_name}' is not authorized.")
        if limit <= 0:
            raise ValueError("Limit must be positive.")
 
        query = f"SELECT * FROM {clean_table_name} LIMIT ?;"
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as error:
            raise RuntimeError(f"Query failed on '{table_name}': {error}")
 
    def get_category_by_id(self, category_id: int) -> dict | None:
        query = "SELECT * FROM Categories WHERE CategoryID = ?;"
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (category_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as error:
            raise RuntimeError(f"Failed to fetch category {category_id}: {error}")
 
    def get_product_by_id(self, product_id: int) -> dict | None:
        query = "SELECT * FROM Products WHERE ProductID = ?;"
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (product_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as error:
            raise RuntimeError(f"Failed to fetch product {product_id}: {error}")