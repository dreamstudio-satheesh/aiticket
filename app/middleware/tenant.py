from contextvars import ContextVar
from typing import Optional

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security import decode_token

# Context variable to store current tenant_id
current_tenant_id: ContextVar[Optional[int]] = ContextVar("current_tenant_id", default=None)


def get_tenant_id() -> Optional[int]:
    """Get current tenant_id from context."""
    return current_tenant_id.get()


def set_tenant_id(tenant_id: int) -> None:
    """Set current tenant_id in context."""
    current_tenant_id.set(tenant_id)


class TenantMiddleware(BaseHTTPMiddleware):
    """Extract tenant_id from JWT and set in context for all requests."""

    EXCLUDED_PATHS = {"/health", "/docs", "/redoc", "/openapi.json", "/api/v1/", "/api/v1/auth/login", "/api/v1/auth/register"}

    async def dispatch(self, request: Request, call_next):
        # Skip tenant check for excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = decode_token(token)
            if payload and "tenant_id" in payload:
                set_tenant_id(payload["tenant_id"])

        response = await call_next(request)
        current_tenant_id.set(None)  # Reset after request
        return response
