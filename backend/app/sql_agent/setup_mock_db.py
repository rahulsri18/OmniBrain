"""
setup_mock_db.py

Day 8 - M1 Task:
Setup a mock database (SQLite) schema for historical stock data 
and populate it with realistic test data.
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import random
from backend.app.logger import logger

# Project Base Path Setup
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "stock_history.db"


def create_schema(cursor: sqlite3.Cursor) -> None:
    """Create companies and stock_prices tables."""
    
    # 1. Companies Master Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS companies (
        company_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT UNIQUE NOT NULL,
        company_name TEXT NOT NULL,
        sector TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Historical Stock Prices Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stock_prices (
        price_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        trade_date DATE NOT NULL,
        open_price REAL NOT NULL,
        high_price REAL NOT NULL,
        low_price REAL NOT NULL,
        close_price REAL NOT NULL,
        volume INTEGER NOT NULL,
        FOREIGN KEY (ticker) REFERENCES companies (ticker),
        UNIQUE(ticker, trade_date)
    );
    """)

    logger.info("Database schema created successfully.")


def populate_test_data(cursor: sqlite3.Cursor) -> None:
    """Populate mock companies and generated historical stock prices."""

    # Mock Companies
    companies = [
        ("AAPL", "Apple Inc.", "Technology"),
        ("MSFT", "Microsoft Corporation", "Technology"),
        ("GOOGL", "Alphabet Inc.", "Communication Services"),
        ("AMZN", "Amazon.com Inc.", "Consumer Discretionary"),
        ("NVDA", "NVIDIA Corporation", "Technology"),
        ("TSLA", "Tesla Inc.", "Automotive"),
    ]

    cursor.executemany("""
    INSERT OR IGNORE INTO companies (ticker, company_name, sector)
    VALUES (?, ?, ?);
    """, companies)

    # Generate Mock Historical Daily Stock Data (Past 30 Days)
    today = datetime.now().date()
    base_prices = {
        "AAPL": 180.0,
        "MSFT": 420.0,
        "GOOGL": 175.0,
        "AMZN": 185.0,
        "NVDA": 120.0,
        "TSLA": 240.0,
    }

    stock_records = []
    for ticker, base_price in base_prices.items():
        current_price = base_price
        for i in range(30, -1, -1):
            trade_date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            
            # Simple Random Walk Model for realistic OHLC data
            daily_change = random.uniform(-0.03, 0.035)
            open_p = round(current_price, 2)
            close_p = round(open_p * (1 + daily_change), 2)
            high_p = round(max(open_p, close_p) + random.uniform(0.5, 2.5), 2)
            low_p = round(min(open_p, close_p) - random.uniform(0.5, 2.5), 2)
            volume = random.randint(5_000_000, 50_000_000)

            stock_records.append((ticker, trade_date, open_p, high_p, low_p, close_p, volume))
            current_price = close_p  # Next day starts close to previous close

    cursor.executemany("""
    INSERT OR IGNORE INTO stock_prices (ticker, trade_date, open_price, high_price, low_price, close_price, volume)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, stock_records)

    logger.info(f"Populated database with {len(companies)} companies and {len(stock_records)} historical stock price rows.")


def init_mock_db() -> Path:
    """Initialize the directory, schema, and seed data."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        create_schema(cursor)
        populate_test_data(cursor)
        conn.commit()
        logger.info(f"Mock Stock Database ready at: {DB_PATH.resolve()}")
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to initialize mock database: {e}")
        raise e
    finally:
        conn.close()

    return DB_PATH


if __name__ == "__main__":
    init_mock_db()