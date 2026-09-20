import sqlite3
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.sql_connect import NorthwindDatabase

TEST_API_KEY = "test-secret-key"
HEADERS = {"X-API-Key": TEST_API_KEY}


@pytest.fixture(autouse=True)
def mock_env_api_key(monkeypatch):
    monkeypatch.setenv("API_KEY", TEST_API_KEY)


@pytest.fixture
def seeded_db_path(tmp_path: Path) -> Path:
    db_path = tmp_path / "northwind_test.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE Categories (
            CategoryID INTEGER PRIMARY KEY,
            CategoryName TEXT NOT NULL,
            Description TEXT
        );
        CREATE TABLE Suppliers (
            SupplierID INTEGER PRIMARY KEY,
            SupplierName TEXT NOT NULL,
            ContactName TEXT,
            Address TEXT,
            City TEXT,
            PostalCode TEXT,
            Country TEXT,
            Phone TEXT
        );
        CREATE TABLE Products (
            ProductID INTEGER PRIMARY KEY,
            ProductName TEXT NOT NULL,
            Unit TEXT,
            Price REAL,
            CategoryID INTEGER,
            SupplierID INTEGER
        );
        CREATE TABLE Employees (
            EmployeeID INTEGER PRIMARY KEY,
            LastName TEXT NOT NULL,
            FirstName TEXT,
            BirthDate TEXT,
            Photo TEXT,
            Notes TEXT
        );
        CREATE TABLE Shippers (
            ShipperID INTEGER PRIMARY KEY,
            ShipperName TEXT NOT NULL,
            Phone TEXT
        );
        CREATE TABLE Customers (
            CustomerID INTEGER PRIMARY KEY,
            CustomerName TEXT NOT NULL,
            ContactName TEXT,
            Address TEXT,
            City TEXT,
            PostalCode TEXT,
            Country TEXT
        );
        CREATE TABLE Orders (
            OrderID INTEGER PRIMARY KEY,
            CustomerID INTEGER,
            EmployeeID INTEGER,
            OrderDate TEXT,
            ShipperID INTEGER
        );
        CREATE TABLE OrderDetails (
            OrderDetailID INTEGER PRIMARY KEY,
            OrderID INTEGER,
            ProductID INTEGER,
            Quantity INTEGER
        );
 
        INSERT INTO Categories (CategoryID, CategoryName, Description) VALUES
            (1, 'Beverages', 'Soft drinks, coffees, teas'),
            (2, 'Condiments', 'Sweet and savory sauces');
 
        INSERT INTO Suppliers (SupplierID, SupplierName, ContactName, Address, City, PostalCode, Country, Phone) VALUES
            (1, 'Exotic Liquids', 'Charlotte Cooper', '49 Gilbert St.', 'London', 'EC1 4SD', 'UK', '(171) 555-2222'),
            (2, 'New Orleans Cajun Delights', 'Shelley Burke', 'P.O. Box 78934', 'New Orleans', '70117', 'USA', '(100) 555-4822');
 
        INSERT INTO Products (ProductID, ProductName, Unit, Price, CategoryID, SupplierID) VALUES
            (1, 'Chai', '10 boxes x 20 bags', 18.0, 1, 1),
            (2, 'Chang', '24 - 12 oz bottles', 19.0, 1, 1),
            (3, 'Aniseed Syrup', '12 - 550 ml bottles', 10.0, 2, 2);
 
        INSERT INTO Employees (EmployeeID, LastName, FirstName, BirthDate, Photo, Notes) VALUES
            (1, 'Davolio', 'Nancy', '1968-12-08', 'EmpID1.pic', 'BA in psychology'),
            (2, 'Fuller', 'Andrew', '1952-02-19', 'EmpID2.pic', 'PhD in international marketing');
 
        INSERT INTO Shippers (ShipperID, ShipperName, Phone) VALUES
            (1, 'Speedy Express', '(503) 555-9831'),
            (2, 'United Package', '(503) 555-3199');
 
        INSERT INTO Customers (CustomerID, CustomerName, ContactName, Address, City, PostalCode, Country) VALUES
            (1, 'Alfreds Futterkiste', 'Maria Anders', 'Obere Str. 57', 'Berlin', '12209', 'Germany'),
            (2, 'Ana Trujillo Emparedados', 'Ana Trujillo', 'Avda. de la Constitucion 2222', 'Mexico D.F.', '05021', 'Mexico');
 
        INSERT INTO Orders (OrderID, CustomerID, EmployeeID, OrderDate, ShipperID) VALUES
            (1, 1, 1, '1996-07-04', 1),
            (2, 2, 2, '1996-07-05', 2);
 
        INSERT INTO OrderDetails (OrderDetailID, OrderID, ProductID, Quantity) VALUES
            (1, 1, 1, 10),
            (2, 1, 2, 5);
        """
    )
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def test_db(seeded_db_path: Path) -> NorthwindDatabase:
    return NorthwindDatabase(db_path=seeded_db_path)


@pytest.fixture
def client(test_db: NorthwindDatabase) -> Generator[TestClient]:
    app.state.db = test_db
    yield TestClient(app)
    app.state.db = None
