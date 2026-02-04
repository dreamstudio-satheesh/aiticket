"""Run this script to seed default prompt templates."""
from app.db.session import SessionLocal
from app.services.prompts import seed_default_prompts

if __name__ == "__main__":
    print("Seeding default prompt templates...")
    db = SessionLocal()
    try:
        count = seed_default_prompts(db)
        print(f"Created {count} prompt templates")
    finally:
        db.close()
    print("Done!")
