import sys
import os

# Add the backend directory to sys.path so the module tree resolves correctly.
_here = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(_here)
sys.path.insert(0, backend_dir)

import traceback
from fastapi import FastAPI
from fastapi.responses import JSONResponse

try:
    from main import app
except Exception as e:
    app = FastAPI()
    error_msg = traceback.format_exc()
    @app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
    async def catch_all(path_name: str):
        return JSONResponse(status_code=500, content={"error": "Init Error", "traceback": error_msg})
