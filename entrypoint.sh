#!/bin/bash
set -e

echo "==> Initializing database tables..."
python init_database.py

# Only seed if DB is fresh (no tenants exist yet = new volume)
TENANT_COUNT=$(python -c "
from app.db.session import SessionLocal
from app.models import Tenant
db = SessionLocal()
print(db.query(Tenant).count())
db.close()
")

if [ "$TENANT_COUNT" = "0" ]; then
  echo "==> Fresh database detected, seeding..."
  python seed_prompts.py
  python seed_users.py
else
  echo "==> Database already seeded ($TENANT_COUNT tenants), skipping."
fi

echo "==> Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
