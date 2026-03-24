import sys
import os

# Add the backend directory to sys.path so 'app' can be imported correctly.
sys.path.insert(0, os.path.dirname(__file__))

from app.main import app
