#!/bin/bash
set -e

echo "==> Initializing database tables..."
python init_database.py

# Always seed prompts (idempotent - skips existing)
echo "==> Ensuring default prompts exist..."
python seed_prompts.py

# Only seed users/tenant if DB is fresh
TENANT_COUNT=$(python -c "
from app.db.session import SessionLocal
from app.models import Tenant
db = SessionLocal()
print(db.query(Tenant).count())
db.close()
")

if [ "$TENANT_COUNT" = "0" ]; then
  echo "==> Fresh database detected, seeding demo tenant..."
  python seed_users.py
else
  echo "==> Database has $TENANT_COUNT tenant(s), skipping user seed."
fi

echo "==> Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
