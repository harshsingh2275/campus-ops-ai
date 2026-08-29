"""
dependencies/__init__.py
"""
from .auth import get_current_user, require_admin

__all__ = ["get_current_user", "require_admin"]
