from typing import TypeVar, Generic, Type, Optional, List
from sqlalchemy.orm import Session, Query
from sqlalchemy import and_

from app.middleware.tenant import get_tenant_id

T = TypeVar("T")


class TenantQuery(Generic[T]):
    """
    Helper class for tenant-isolated database queries.
    Automatically filters all queries by current tenant_id.
    """

    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model
        self.tenant_id = get_tenant_id()

    def _base_query(self) -> Query:
        """Base query with tenant filter applied."""
        if not hasattr(self.model, "tenant_id"):
            raise ValueError(f"Model {self.model.__name__} does not have tenant_id field")
        if self.tenant_id is None:
            raise ValueError("No tenant context set")
        return self.db.query(self.model).filter(self.model.tenant_id == self.tenant_id)

    def all(self) -> List[T]:
        return self._base_query().all()

    def get(self, id: int) -> Optional[T]:
        return self._base_query().filter(self.model.id == id).first()

    def filter(self, *args) -> Query:
        return self._base_query().filter(*args)

    def first(self) -> Optional[T]:
        return self._base_query().first()

    def count(self) -> int:
        return self._base_query().count()

    def create(self, **kwargs) -> T:
        """Create a new record with tenant_id automatically set."""
        obj = self.model(tenant_id=self.tenant_id, **kwargs)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, id: int) -> bool:
        """Delete by id (only within tenant scope)."""
        obj = self.get(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False
