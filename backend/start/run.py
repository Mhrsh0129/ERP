"""
Local development runner.
Usage: python run.py  (from the backend/start/ directory)
"""

import os
import sys
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", os.getenv("FLASK_PORT", 5000)))
    
    # Get the parent 'backend' directory explicitly
    _here = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.dirname(_here)
    
    sys.path.insert(0, app_dir)
    os.chdir(app_dir) # Make sure uvicorn operates out of backend/
    
    print("🚀 ERP — FastAPI")
    print(f"   http://localhost:{port}")
    print(f"   http://localhost:{port}/docs  ← API docs")
    print(f"   [Serving from {app_dir}]")
    
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
