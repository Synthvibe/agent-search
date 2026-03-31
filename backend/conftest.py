# conftest.py — root-level; ensures 'app' package is importable when running pytest from backend/
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
