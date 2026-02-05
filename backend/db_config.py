from mysql.connector import Error, pooling
import os
from dotenv import load_dotenv


env_path = os.path.abspath(".env")
load_dotenv(dotenv_path=env_path, override=True)


host = os.getenv("DB_HOST", "gateway01.ap-southeast-1.prod.aws.tidbcloud.com")
if host:
    host = host.strip()

user = os.getenv("DB_USER", "2RsUE3FehSmWPK2.root")
if user:
    user = user.strip()

db_config = {
    "host": host,
    "user": user,
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME", "test"),
    "port": int(os.getenv("DB_PORT", 4000)),
    "ssl_disabled": False,
    "autocommit": True,
}

connection_pool = None


def init_connection_pool():
    global connection_pool
    try:
        connection_pool = pooling.MySQLConnectionPool(
            pool_name="erp_pool", pool_size=5, pool_reset_session=True, **db_config
        )
        print("✅ Database connection pool created successfully")
        return True
    except Error as e:
        print(f"❌ Error creating connection pool: {e}")
        return False


def init_db_schema():
    """Ensures necessary tables and columns exist in the database."""
    conn = None
    try:
        conn = get_db_connection()
        if conn and conn.is_connected():
            cursor = conn.cursor()

            # 1. Create Tables (if they don't exist)

            # Incoming Stock
            cursor.execute("""
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
                    tax_amount DECIMAL(10,2) GENERATED ALWAYS AS ((quantity * price_per_unit) * (tax_percent / 100)) VIRTUAL,
                    amount DECIMAL(10,2) GENERATED ALWAYS AS ((quantity * price_per_unit) + ((quantity * price_per_unit) * (tax_percent / 100))) VIRTUAL,
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

            # Outgoing Stock
            cursor.execute("""
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

            # Payment Transactions (Incoming)
            cursor.execute("""
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

            # Sales Payments (Outgoing)
            cursor.execute("""
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

            # Product Details
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS product_details (
                    product_name VARCHAR(255) PRIMARY KEY,
                    details TEXT
                )
            """)

            # Live Inventory View (Simplified for TiDB/MySQL compatibility)
            cursor.execute("DROP VIEW IF EXISTS live_inventory")
            cursor.execute("""
                CREATE VIEW live_inventory AS
                SELECT 
                    T.product_name,
                    MAX(T.unit) as unit, 
                    SUM(T.quantity) as current_stock
                FROM (
                    SELECT product_name, quantity, unit FROM incoming_stock
                    UNION ALL
                    SELECT product_name, -quantity, unit FROM outgoing_stock
                ) T
                GROUP BY T.product_name
            """)

            # --- Legacy Migration / specific column checks ---
            # (Kept to ensure older databases are patched correctly)

            # Check and update outgoing_stock table
            cursor.execute("SHOW COLUMNS FROM outgoing_stock")
            existing_cols = [col[0] for col in cursor.fetchall()]

            # Add invoice_no if missing
            if "invoice_no" not in existing_cols:
                print("Adding invoice_no to outgoing_stock...")
                cursor.execute(
                    "ALTER TABLE outgoing_stock ADD COLUMN invoice_no VARCHAR(50) AFTER id"
                )

            # Add delivery_date if missing
            if "delivery_date" not in existing_cols:
                print("Adding delivery_date to outgoing_stock...")
                cursor.execute(
                    "ALTER TABLE outgoing_stock ADD COLUMN delivery_date DATE AFTER payment_date"
                )

            # Add tax if missing
            if "tax" not in existing_cols:
                print("Adding tax to outgoing_stock...")
                cursor.execute(
                    "ALTER TABLE outgoing_stock ADD COLUMN tax DECIMAL(10,2) DEFAULT 0.00 AFTER total_amount"
                )

            # Add tax_percentage if missing
            if "tax_percentage" not in existing_cols:
                print("Adding tax_percentage to outgoing_stock...")
                # Try to add after tax, otherwise just append
                if "tax" in existing_cols:
                    cursor.execute(
                        "ALTER TABLE outgoing_stock ADD COLUMN tax_percentage DECIMAL(5,2) DEFAULT 5.00 AFTER tax"
                    )
                else:
                    cursor.execute(
                        "ALTER TABLE outgoing_stock ADD COLUMN tax_percentage DECIMAL(5,2) DEFAULT 5.00"
                    )

            # Add product_photo if missing
            if "product_photo" not in existing_cols:
                print("Adding product_photo to outgoing_stock...")
                # Add after bill_photo if it exists, otherwise at end
                if "bill_photo" in existing_cols:
                    cursor.execute(
                        "ALTER TABLE outgoing_stock ADD COLUMN product_photo LONGBLOB AFTER bill_photo"
                    )
                else:
                    cursor.execute(
                        "ALTER TABLE outgoing_stock ADD COLUMN product_photo LONGBLOB"
                    )

            # Add discount_amount if missing
            if "discount_amount" not in existing_cols:
                print("Adding discount_amount to outgoing_stock...")
                cursor.execute(
                    "ALTER TABLE outgoing_stock ADD COLUMN discount_amount DECIMAL(10,2) DEFAULT 0.00 AFTER tax_percentage"
                )

            # Ensure total_amount is a standard DECIMAL column (not generated)
            try:
                cursor.execute(
                    "ALTER TABLE outgoing_stock MODIFY COLUMN total_amount DECIMAL(10,2) NOT NULL"
                )
            except Exception:
                # Ignore if it's already correct
                pass

            # Check and update incoming_stock table
            cursor.execute("SHOW COLUMNS FROM incoming_stock")
            incoming_cols = [col[0] for col in cursor.fetchall()]

            # Add discount_amount if missing
            if "discount_amount" not in incoming_cols:
                print("Adding discount_amount to incoming_stock...")
                cursor.execute(
                    "ALTER TABLE incoming_stock ADD COLUMN discount_amount DECIMAL(10,2) DEFAULT 0.00 AFTER tax_percent"
                )

            conn.commit()
            print("✅ Database schema check/init completed.")

            cursor.close()
            conn.close()
    except Exception as e:
        print(f"❌ Schema check error: {e}")


def get_db_connection():
    try:
        if connection_pool is None:
            init_connection_pool()
        connection = connection_pool.get_connection()
        return connection
    except Error as e:
        print(f"❌ Error getting connection from pool: {e}")
        return None


def test_connection():
    try:
        conn = get_db_connection()
        if conn and conn.is_connected():
            cursor = conn.cursor()
            cursor.execute("SELECT DATABASE();")
            db_name = cursor.fetchone()
            cursor.close()
            conn.close()
            print(f"✅ Connected to database: {db_name[0]}")
            return True
        return False
    except Error as e:
        print(f"❌ Database connection test failed: {e}")
        return False
