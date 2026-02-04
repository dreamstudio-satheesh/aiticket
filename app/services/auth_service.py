from typing import Optional
from sqlalchemy.orm import Session

from app.models import User, Tenant, UserRole
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.auth import RegisterRequest, UserCreate


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def create_user(db: Session, tenant_id: int, user_data: UserCreate) -> User:
    user = User(
        tenant_id=tenant_id,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def register_user(db: Session, data: RegisterRequest) -> Optional[User]:
    # Check if tenant exists
    tenant = db.query(Tenant).filter(Tenant.slug == data.tenant_slug).first()
    if not tenant:
        return None

    # Check if email already exists
    if db.query(User).filter(User.email == data.email).first():
        return None

    user = User(
        tenant_id=tenant.id,
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=UserRole.SUPPORT_AGENT,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def generate_token(user: User) -> str:
    return create_access_token({"sub": str(user.id), "tenant_id": user.tenant_id})
