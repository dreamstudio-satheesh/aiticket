"""Run this script to create all database tables."""
from app.db.session import init_db

if __name__ == "__main__":
    print("Creating database tables...")
    init_db()
    print("Done!")
