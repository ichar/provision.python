import os
import sys

root = os.path.dirname(os.path.abspath(__file__))

if root not in sys.path:
    sys.path.insert(0, root)

from app import create_app
app = create_app(os.getenv('APP_CONFIG') or 'production')
