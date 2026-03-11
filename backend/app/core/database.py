"""
database.py — Manages the MySQL database connection.

This file does three things:
  1. Reads DB credentials from the .env file
  2. Creates a "connection pool" (a reusable set of DB connections)
  3. Creates all the tables in the database when the app starts
"""

# mysql.connector is the library that lets Python talk to MySQL
from mysql.connector import pooling
from dotenv import load_dotenv  # Reads our .env file into environment variables
import os

# We look for .env in backend/ first, then fall back to project root
_here = os.path.dirname(os.path.abspath(__file__))
_env = os.path.join(_here, "..", "..", ".env")
load_dotenv(dotenv_path=_env if os.path.exists(_env) else None, override=True)


# ── DB Config ─────────────────────────────────────────────────────────────────
# os.getenv("KEY", "default") reads a value from the .env file.
# If the key isn't found, it uses the second argument as a default.
db_config = {
    "host": (
        os.getenv("DB_HOST", "gateway01.ap-southeast-1.prod.aws.tidbcloud.com") or ""
    ).strip(),
    "user": (os.getenv("DB_USER", "2RsUE3FehSmWPK2.root") or "").strip(),
    "password": os.getenv("DB_PASSWORD"),  # No default — must be in .env
    "database": (os.getenv("DB_NAME", "test") or "").strip(),
    "port": int(os.getenv("DB_PORT", 4000)),
    "ssl_disabled": False,  # TiDB requires SSL
    "autocommit": True,
}

# This will hold our connection pool once init_connection_pool() is called
_pool = None


def init_connection_pool():
    """
    Creates a pool of 5 MySQL connections.

    Why a pool? Opening a new DB connection for every API request is slow.
    A pool keeps connections open and reuses them, which is much faster.
    """
    global _pool
    _pool = pooling.MySQLConnectionPool(pool_name="erp_pool", pool_size=5, **db_config)
    print("✅ Connection pool ready")


def get_db_connection():
    """
    Gets one connection from the pool.
    After using it, call conn.close() to return it to the pool.
    """
    global _pool
    if _pool is None:
        init_connection_pool()
    return _pool.get_connection()


def test_connection():
    """Simple check: can we connect and run a query? Returns True/False."""
    conn = get_db_connection()
    if not conn or not conn.is_connected():
        return False
    cur = conn.cursor()
    cur.execute("SELECT DATABASE();")
    db_name = cur.fetchone()
    cur.close()
    conn.close()
    print(f"✅ Connected to database: {db_name[0]}")
    return True


def init_db_schema():
    """
    Creates all tables and views if they don't exist, and adds any missing columns.

    CREATE TABLE IF NOT EXISTS = only runs if the table isn't already there.
    This is safe to call every time the app starts.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # ── Table: incoming_stock ─────────────────────────────────────────────────
    # Stores every purchase / inward shipment
    cur.execute("""
        CREATE TABLE IF NOT EXISTS incoming_stock (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_name VARCHAR(255) NOT NULL,
            source_name VARCHAR(255),
            date_of_purchase DATE,
            quantity DECIMAL(10,2) DEFAULT 0,
            unit VARCHAR(50),
            price_per_unit DECIMAL(10,2) DEFAULT 0,
            tax_percent DECIMAL(5,2) DEFAULT 0,
            discount_amount DECIMAL(10,2) DEFAULT 0.00,
            tax_amount DECIMAL(10,2) GENERATED ALWAYS AS
                ((quantity * price_per_unit) * (tax_percent / 100)) VIRTUAL,
            amount DECIMAL(10,2) GENERATED ALWAYS AS
                ((quantity * price_per_unit) + ((quantity * price_per_unit) * (tax_percent / 100))) VIRTUAL,
            payment_status VARCHAR(50) DEFAULT 'pending',
            amount_paid DECIMAL(10,2) DEFAULT 0,
            payment_type VARCHAR(50),
            payment_date DATE,
            delivery_date DATE,
            product_photo LONGBLOB,
            bill_photo LONGBLOB,
            bilti_photo LONGBLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Table: outgoing_stock ─────────────────────────────────────────────────
    # Stores every sale / outward shipment
    cur.execute("""
        CREATE TABLE IF NOT EXISTS outgoing_stock (
            id INT AUTO_INCREMENT PRIMARY KEY,
            invoice_no VARCHAR(50),
            product_name VARCHAR(255) NOT NULL,
            customer_name VARCHAR(255),
            gst_number VARCHAR(50),
            date_of_sale DATE,
            quantity DECIMAL(10,2) DEFAULT 0,
            unit VARCHAR(50),
            price_per_unit DECIMAL(10,2) DEFAULT 0,
            total_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
            tax DECIMAL(10,2) DEFAULT 0,
            tax_percentage DECIMAL(5,2) DEFAULT 0,
            discount_amount DECIMAL(10,2) DEFAULT 0.00,
            payment_status VARCHAR(50) DEFAULT 'pending',
            amount_paid DECIMAL(10,2) DEFAULT 0,
            payment_type VARCHAR(50),
            payment_date DATE,
            delivery_date DATE,
            bill_photo LONGBLOB,
            product_photo LONGBLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Table: payment_transactions ───────────────────────────────────────────
    # Each row is one payment instalment against a purchase (incoming_stock)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS payment_transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            stock_id INT,
            amount DECIMAL(10,2) NOT NULL,
            payment_date DATE,
            payment_type VARCHAR(50),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES incoming_stock(id) ON DELETE CASCADE
        )
    """)

    # ── Table: sales_payments ─────────────────────────────────────────────────
    # Each row is one payment instalment against a sale (outgoing_stock)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sales_payments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            stock_id INT,
            amount DECIMAL(10,2) NOT NULL,
            payment_date DATE,
            payment_type VARCHAR(50),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_id) REFERENCES outgoing_stock(id) ON DELETE CASCADE
        )
    """)

    # ── Table: product_details ────────────────────────────────────────────────
    # Stores extra notes/details per product name
    cur.execute("""
        CREATE TABLE IF NOT EXISTS product_details (
            product_name VARCHAR(255) PRIMARY KEY,
            details TEXT
        )
    """)

    # ── View: live_inventory ──────────────────────────────────────────────────
    # A VIEW is like a virtual table. Here we calculate current stock by
    # adding all purchases and subtracting all sales for each product.
    cur.execute("DROP VIEW IF EXISTS live_inventory")
    cur.execute("""
        CREATE VIEW live_inventory AS
        SELECT T.product_name, MAX(T.unit) AS unit, SUM(T.quantity) AS current_stock
        FROM (
            SELECT product_name,  quantity, unit FROM incoming_stock
            UNION ALL
            SELECT product_name, -quantity, unit FROM outgoing_stock
        ) T
        GROUP BY T.product_name
    """)

    # ── Legacy migrations ─────────────────────────────────────────────────────
    # If an older version of this app was running, some columns might be missing.
    # We check the existing columns and add any that are absent.
    cur.execute("SHOW COLUMNS FROM outgoing_stock")
    out_cols = [c[0] for c in cur.fetchall()]

    _add_col(cur, "outgoing_stock", out_cols, "invoice_no", "VARCHAR(50)", "AFTER id")
    _add_col(
        cur, "outgoing_stock", out_cols, "delivery_date", "DATE", "AFTER payment_date"
    )
    _add_col(
        cur,
        "outgoing_stock",
        out_cols,
        "tax",
        "DECIMAL(10,2) DEFAULT 0.00",
        "AFTER total_amount",
    )
    _add_col(
        cur,
        "outgoing_stock",
        out_cols,
        "product_photo",
        "LONGBLOB",
        "AFTER bill_photo" if "bill_photo" in out_cols else "",
    )
    _add_col(
        cur,
        "outgoing_stock",
        out_cols,
        "discount_amount",
        "DECIMAL(10,2) DEFAULT 0.00",
        "AFTER tax_percentage" if "tax_percentage" in out_cols else "",
    )

    if "tax_percentage" not in out_cols:
        after = "AFTER tax" if "tax" in out_cols else ""
        cur.execute(
            f"ALTER TABLE outgoing_stock ADD COLUMN tax_percentage DECIMAL(5,2) DEFAULT 5.00 {after}"
        )

    cur.execute("SHOW COLUMNS FROM incoming_stock")
    in_cols = [c[0] for c in cur.fetchall()]
    _add_col(
        cur,
        "incoming_stock",
        in_cols,
        "discount_amount",
        "DECIMAL(10,2) DEFAULT 0.00",
        "AFTER tax_percent" if "tax_percent" in in_cols else "",
    )

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Schema ready")


def _add_col(cur, table, existing, col, definition, position=""):
    """Adds a column only if it doesn't already exist."""
    if col not in existing:
        print(f"  Adding missing column '{col}' to '{table}'...")
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {definition} {position}")
