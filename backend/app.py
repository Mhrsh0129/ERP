import os

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from db_config import init_connection_pool, test_connection, init_db_schema
from models import IncomingStock, OutgoingStock, LiveInventory, Dashboard

# Use absolute path for static folder to avoid relative path issues
current_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(current_dir, "..", "frontend")
app = Flask(__name__, static_folder=frontend_dir, static_url_path="")
CORS(app)

# Disable all caching for development
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB max file size

# Initialize DB
# Initialize DB
print("🚀 Starting Flask Application...")
print(f"DEBUG: DB_HOST = {os.getenv('DB_HOST')}")
print(f"DEBUG: DB_USER = {os.getenv('DB_USER')}")
print(f"DEBUG: DB_PORT = {os.getenv('DB_PORT')}")
# Do NOT print password!

try:
    init_connection_pool()
    init_db_schema()
    print("✅ Database initialized successfully.")
except Exception as e:
    print(f"❌ Critical Error during DB init: {e}")


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html", mimetype="text/html")


@app.route("/favicon.ico")
def favicon():
    return "", 204


@app.route("/<path:path>")
def serve_static(path):
    try:
        file_path = os.path.join(app.static_folder, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            # Determine mimetype
            if path.endswith(".html"):
                mimetype = "text/html"
            elif path.endswith(".css"):
                mimetype = "text/css"
            elif path.endswith(".js"):
                mimetype = "application/javascript"
            elif path.endswith(".json"):
                mimetype = "application/json"
            elif path.endswith(".png"):
                mimetype = "image/png"
            elif path.endswith(".jpg") or path.endswith(".jpeg"):
                mimetype = "image/jpeg"
            elif path.endswith(".ico"):
                mimetype = "image/x-icon"
            elif path.endswith(".webp"):
                mimetype = "image/webp"
            elif path.endswith(".svg"):
                mimetype = "image/svg+xml"
            else:
                mimetype = None

            # Set cache headers for service worker (no cache)
            if path == "service-worker.js":
                response = send_from_directory(
                    app.static_folder, path, mimetype=mimetype
                )
                response.headers["Cache-Control"] = (
                    "no-cache, no-store, must-revalidate"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response

            return send_from_directory(app.static_folder, path, mimetype=mimetype)
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        print(f"Error serving {path}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/test-connection", methods=["GET"])
def test_db_connection():
    if test_connection():
        return jsonify({"success": True, "message": "Database connected successfully"})
    return jsonify({"success": False, "message": "Database connection failed"}), 500


@app.route("/api/dashboard", methods=["GET"])
def get_dashboard():
    result = Dashboard.get_stats()
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 500


@app.route("/api/incoming-stock", methods=["GET"])
def get_incoming_stock():
    search_query = request.args.get("search", "")
    if search_query:
        result = IncomingStock.search(search_query)
    else:
        result = IncomingStock.get_all()

    if result["success"]:
        return jsonify(result)
    return jsonify(result), 500


@app.route("/api/incoming-stock/<int:stock_id>", methods=["GET"])
def get_incoming_stock_by_id(stock_id):
    result = IncomingStock.get_by_id(stock_id)
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 404


@app.route("/api/incoming-stock", methods=["POST"])
def create_incoming_stock():
    data = request.get_json()
    result = IncomingStock.create(data)
    if result["success"]:
        return jsonify(result), 201
    return jsonify(result), 400


@app.route("/api/incoming-stock/<int:stock_id>", methods=["PUT"])
def update_incoming_stock(stock_id):
    data = request.get_json()
    result = IncomingStock.update(stock_id, data)
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 400


@app.route("/api/incoming-stock/<int:stock_id>", methods=["DELETE"])
def delete_incoming_stock(stock_id):
    result = IncomingStock.delete(stock_id)
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 400


# Payment Transaction Routes


@app.route("/api/incoming-stock/<int:stock_id>/payments", methods=["GET"])
def get_stock_payments(stock_id):
    result = IncomingStock.get_payments(stock_id)
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 500


@app.route("/api/incoming-stock/<int:stock_id>/payments", methods=["POST"])
def add_stock_payment(stock_id):
    data = request.get_json()
    result = IncomingStock.add_payment(stock_id, data)
    if result["success"]:
        return jsonify(result), 201
    return jsonify(result), 400


@app.route("/api/payments/<int:payment_id>", methods=["DELETE"])
def delete_payment(payment_id):
    result = IncomingStock.delete_payment(payment_id)
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 400


@app.route("/api/outgoing-stock", methods=["GET"])
def get_outgoing_stock():
    search_query = request.args.get("search", "")
    if search_query:
        result = OutgoingStock.search(search_query)
    else:
        result = OutgoingStock.get_all()

    if result["success"]:
        return jsonify(result)
    return jsonify(result), 500


@app.route("/api/outgoing-stock/<int:stock_id>", methods=["GET"])
def get_outgoing_stock_by_id(stock_id):
    result = OutgoingStock.get_by_id(stock_id)
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 404


@app.route("/api/outgoing-stock", methods=["POST"])
def create_outgoing_stock():
    data = request.get_json()
    result = OutgoingStock.create(data)
    if result["success"]:
        return jsonify(result), 201
    return jsonify(result), 400


@app.route("/api/outgoing-stock/<int:stock_id>", methods=["PUT"])
def update_outgoing_stock(stock_id):
    data = request.get_json()
    result = OutgoingStock.update(stock_id, data)
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 400


@app.route("/api/outgoing-stock/<int:stock_id>", methods=["DELETE"])
def delete_outgoing_stock(stock_id):
    result = OutgoingStock.delete(stock_id)
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 400


@app.route("/api/outgoing-stock/<int:stock_id>/payments", methods=["GET"])
def get_sales_payments(stock_id):
    result = OutgoingStock.get_payments(stock_id)
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 500


@app.route("/api/outgoing-stock/<int:stock_id>/payments", methods=["POST"])
def add_sales_payment(stock_id):
    data = request.get_json()
    result = OutgoingStock.add_payment(stock_id, data)
    if result["success"]:
        return jsonify(result), 201
    return jsonify(result), 400


@app.route("/api/sales-payments/<int:payment_id>", methods=["DELETE"])
def delete_sales_payment(payment_id):
    result = OutgoingStock.delete_payment(payment_id)
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 400


@app.route("/api/inventory", methods=["GET"])
def get_inventory():
    result = LiveInventory.get_all()
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 500


@app.route("/api/inventory/low-stock", methods=["GET"])
def get_low_stock():
    result = LiveInventory.get_low_stock()
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 500


@app.route("/api/inventory/details", methods=["POST"])
def update_product_details():
    data = request.get_json()
    if not data or "product_name" not in data or "details" not in data:
        return jsonify(
            {"success": False, "error": "Missing product_name or details"}
        ), 400

    result = LiveInventory.update_details(data["product_name"], data["details"])
    if result["success"]:
        return jsonify(result)
    return jsonify(result), 500


# Bill Scanning Route (AI-powered)
@app.route("/api/scan-bill", methods=["POST"])
def scan_bill():
    """
    AI-powered bill scanning endpoint.
    Accepts image data and returns extracted bill information.
    """
    try:
        from utils.gemini_scanner import scan_bill_image

        data = request.get_json()

        # Validate request
        if not data or "image" not in data:
            return jsonify({"success": False, "error": "No image data provided"}), 400

        image_data = data.get("image")
        suggested_type = data.get("suggested_type")  # 'incoming' or 'outgoing'

        # Process bill with Gemini AI
        result = scan_bill_image(image_data, suggested_type)

        if result.get("success"):
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except ImportError:
        return jsonify(
            {
                "success": False,
                "error": "Bill scanning feature not available. Please check GEMINI_API_KEY is set.",
            }
        ), 500
    except Exception as e:
        import traceback

        error_trace = traceback.format_exc()
        print("ERROR in /api/scan-bill:")
        print(error_trace)
        return jsonify(
            {"success": False, "error": f"Bill scanning failed: {str(e)}"}
        ), 500


@app.errorhandler(404)
def not_found(e):
    return jsonify({"success": False, "error": "Endpoint not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"success": False, "error": "Internal server error"}), 500


if __name__ == "__main__":
    print("🚀 Starting Jay Shree Traders ERP System...")
    print("=" * 50)

    if init_connection_pool():
        if test_connection():
            port = int(os.getenv("FLASK_PORT", 5000))
            print(f"✅ Server running on http://localhost:{port}")
            print(f"📊 Dashboard: http://localhost:{port}")
            print(f"📦 Incoming Stock: http://localhost:{port}/incoming-stock.html")
            print(f"📤 Outgoing Stock: http://localhost:{port}/outgoing-stock.html")
            print(f"📋 Inventory: http://localhost:{port}/inventory.html")
            print("=" * 50)
            app.run(debug=True, host="0.0.0.0", port=port)
        else:
            print(
                "❌ Database connection test failed. Please check your configuration."
            )
    else:
        print("❌ Failed to initialize database connection pool.")
