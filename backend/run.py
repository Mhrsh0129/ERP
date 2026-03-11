"""
Local development runner.
Usage: python run.py  (from the backend/ directory)
"""

import os
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", os.getenv("FLASK_PORT", 5000)))
    print("🚀 Jay Shree Traders ERP — FastAPI")
    print(f"   http://localhost:{port}")
    print(f"   http://localhost:{port}/docs  ← API docs")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
