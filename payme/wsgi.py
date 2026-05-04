import sys
import os

# Add the project path to sys.path
sys.path.insert(0, '/var/www/nothard/payme')

# Print environment info for debugging
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"sys.path: {sys.path}")

# Import the Flask app
from app import app as application