"""
scripts/set_user_role.py — CLI Script to Upgrade / Manage User Roles
====================================================================

Usage
-----
1. Command-line arguments:
   python scripts/set_user_role.py user@campus.edu admin
   python scripts/set_user_role.py user@campus.edu student

2. Interactive mode (without arguments):
   python scripts/set_user_role.py
"""

import sys
import os

# Ensure backend root is on PYTHONPATH
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.database import SessionLocal, create_db_tables
from app.models.user import User


def list_users(db):
    users = db.query(User).order_by(User.id.asc()).all()
    print("\nExisting Users:")
    print("-" * 65)
    print(f"{'ID':<4} | {'Email':<30} | {'Name':<15} | {'Role':<10}")
    print("-" * 65)
    for u in users:
        print(f"{u.id:<4} | {u.email:<30} | {u.name:<15} | {u.role:<10}")
    print("-" * 65 + "\n")
    return users


def set_user_role(email: str, role: str):
    create_db_tables()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email.strip().lower()).first()
        if not user:
            print(f"[ERROR] User with email '{email}' was not found in the database.")
            list_users(db)
            return False

        old_role = user.role
        user.role = role.strip().lower()
        db.commit()
        db.refresh(user)

        print(f"[SUCCESS] Successfully updated User ID {user.id} ({user.email}):")
        print(f"          Name: {user.name}")
        print(f"          Old Role: {old_role}")
        print(f"          New Role: {user.role}\n")
        return True
    finally:
        db.close()


def main():
    if len(sys.argv) >= 2:
        email = sys.argv[1]
        role = sys.argv[2] if len(sys.argv) >= 3 else "admin"
        set_user_role(email, role)
    else:
        create_db_tables()
        db = SessionLocal()
        users = list_users(db)
        db.close()

        if not users:
            print("[INFO] No users found in database. Register a user first via /register.")
            return

        email = input("Enter user email to update: ").strip()
        if not email:
            print("[ABORTED] No email provided.")
            return

        role = input("Enter new role [default: admin]: ").strip() or "admin"
        set_user_role(email, role)


if __name__ == "__main__":
    main()
