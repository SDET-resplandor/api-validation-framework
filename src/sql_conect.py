import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data_file" / "Northwind.db"


class NorthwindDatabase:
    """Wraps the connection and queries for the Northwind SQLite database."""
    
    ALLOWED_TABLES: set[str] = {
        "orders",
        "products",
        "categories",
        "suppliers"
        
    }

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._validate_db_exists()

    def _validate_db_exists(self) -> None:
        if not self.db_path.exists():
            raise FileNotFoundError(f"Couldn't find the database at '{self.db_path}'")

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # lets us return rows as dicts
        return conn

    def get_table_data(self, table_name: str, limit: int = 10) -> list[dict]:
        """Fetches rows from an allowed table, preventing unauthorized data access."""
        
        clean_table_name = table_name.lower().strip()
        
        if clean_table_name not in self.ALLOWED_TABLES:

            raise ValueError(f"Access denied: '{table_name}' is not an authorized public table.")


        query = f"SELECT * FROM {clean_table_name} LIMIT ?;"

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (limit,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as error:
            raise RuntimeError(f"Query failed on '{table_name}': {error}")

    def get_customer_by_id(self, customer_id: str) -> dict | None:
        """Looks up one customer by ID using a parameterized WHERE clause."""
        query = "SELECT * FROM Customers WHERE CustomerID = ?;"

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (customer_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as error:
            raise RuntimeError(f"Failed to look up customer '{customer_id}': {error}")
        
if __name__ == "__main__":
    db = NorthwindDatabase()

    print("=== SMOKE TEST ===")

    # 1. Allowed Table Test
    customers = db.get_table_data("Customers", limit=2)
    print(f"[OK] Fetched {len(customers)} rows:")
    print(f"     Sample row keys: {list(customers[0].keys())}")
    print(f"     Sample data: {customers[0]}")

    # 2. Parameterized ID Lookup Test
    if customer := db.get_customer_by_id("ALFKI"):
        print(f"[OK] Found Customer: {customer}")

    # 3. Allowlist Security Test
    try:
        db.get_table_data("Employees")
    except ValueError as err:
        print(f"[OK] Access Denied: {err}")