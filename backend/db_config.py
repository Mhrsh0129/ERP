from mysql.connector import Error, pooling
import os
from dotenv import load_dotenv

load_dotenv()

db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME", "jay_shree_traders"),
    "port": int(os.getenv("DB_PORT", 3306)),
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
    """Ensures necessary columns exist in the database."""
    conn = None
    try:
        conn = get_db_connection()
        if conn and conn.is_connected():
            cursor = conn.cursor()

            # Check and update outgoing_stock table
            cursor.execute("SHOW TABLES LIKE 'outgoing_stock'")
            if cursor.fetchone():
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
                # We blindly modify it to be safe (MODIFY is idempotent-ish for type)
                try:
                    cursor.execute(
                        "ALTER TABLE outgoing_stock MODIFY COLUMN total_amount DECIMAL(10,2) NOT NULL"
                    )
                except Exception as e:
                    print(
                        f"Note: Could not modify total_amount (might already be correct): {e}"
                    )

            # Check and update incoming_stock table
            cursor.execute("SHOW TABLES LIKE 'incoming_stock'")
            if cursor.fetchone():
                cursor.execute("SHOW COLUMNS FROM incoming_stock")
                incoming_cols = [col[0] for col in cursor.fetchall()]

                # Add discount_amount if missing
                if "discount_amount" not in incoming_cols:
                    print("Adding discount_amount to incoming_stock...")
                    cursor.execute(
                        "ALTER TABLE incoming_stock ADD COLUMN discount_amount DECIMAL(10,2) DEFAULT 0.00 AFTER tax_percent"
                    )

                # Check and create product_details table
                cursor.execute("SHOW TABLES LIKE 'product_details'")
                if not cursor.fetchone():
                    print("Creating product_details table...")
                    cursor.execute("""
                        CREATE TABLE product_details (
                            product_name VARCHAR(255) PRIMARY KEY,
                            details TEXT
                        )
                    """)

                conn.commit()
                print("✅ Database schema check completed.")
            else:
                print("⚠️ Table 'outgoing_stock' does not exist.")

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
