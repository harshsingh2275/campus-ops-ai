"""
set_role.py — Root convenience wrapper for scripts/set_user_role.py
"""
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from scripts.set_user_role import main

if __name__ == "__main__":
    main()
