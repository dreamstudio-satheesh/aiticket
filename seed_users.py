"""Seed a demo tenant and admin user for testing."""
from app.db.session import SessionLocal
from app.models import Tenant, User, UserRole
from app.core.security import hash_password


def seed():
    db = SessionLocal()
    try:
        # Check if tenant already exists
        tenant = db.query(Tenant).filter(Tenant.slug == "demo").first()
        if not tenant:
            tenant = Tenant(name="Demo Hosting", slug="demo", is_active=True)
            db.add(tenant)
            db.flush()
            print(f"Created tenant: {tenant.name} (id={tenant.id})")
        else:
            print(f"Tenant already exists: {tenant.name} (id={tenant.id})")

        # Check if admin user already exists
        admin = db.query(User).filter(User.email == "admin@demo.com", User.tenant_id == tenant.id).first()
        if not admin:
            admin = User(
                tenant_id=tenant.id,
                email="admin@demo.com",
                hashed_password=hash_password("password"),
                full_name="Admin User",
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin)
            print(f"Created admin user: admin@demo.com / password")
        else:
            print(f"Admin user already exists: {admin.email}")

        # Create a support agent too
        agent = db.query(User).filter(User.email == "agent@demo.com", User.tenant_id == tenant.id).first()
        if not agent:
            agent = User(
                tenant_id=tenant.id,
                email="agent@demo.com",
                hashed_password=hash_password("password"),
                full_name="Support Agent",
                role=UserRole.SUPPORT_AGENT,
                is_active=True,
            )
            db.add(agent)
            print(f"Created support agent: agent@demo.com / password")
        else:
            print(f"Support agent already exists: {agent.email}")

        db.commit()
        print("\nDone! You can now log in with:")
        print("  Email: admin@demo.com  Password: password")
        print("  Email: agent@demo.com  Password: password")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
