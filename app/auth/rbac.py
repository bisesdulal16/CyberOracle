"""
RBAC Enforcement Module
-----------------------
Provides a FastAPI dependency factory that enforces role-based access
control using JWT claims.

Usage
-----
    from app.auth.rbac import require_roles

    @router.get("/secure-endpoint")
    async def endpoint(user=Depends(require_roles("admin", "auditor"))):
        ...

Token format
------------
JWT payload must contain a "role" claim matching one of the roles
defined in docs/threat-modeling/policy.yaml:
    - "admin"
    - "developer"
    - "auditor"

Error codes
-----------
401  No / invalid Authorization header (missing or malformed JWT)
403  Valid token but role not in allowed list
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.jwt_utils import verify_token

# ADDED: import the RBAC permission policy map created in Step 2
from app.auth.permissions import ROLE_PERMISSIONS

from app.auth.policy_loader import get_role_permissions

# HTTPBearer extracts "Authorization: Bearer <token>" from the request
_bearer = HTTPBearer(auto_error=False)


def require_roles(*allowed_roles: str):
    """
    Dependency factory.  Returns a FastAPI dependency that:
      1. Reads the Bearer token from the Authorization header.
      2. Decodes and verifies the JWT.
      3. Checks the "role" claim against `allowed_roles`.
      4. Returns the decoded payload on success.
      5. Raises HTTP 401 / 403 on failure.

    Parameters
    ----------
    *allowed_roles : str
        One or more role strings (e.g. "admin", "auditor").
    """

    async def _enforce(
        credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    ) -> dict:
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Provide a Bearer token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            payload = verify_token(credentials.credentials)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        role = payload.get("role", "")
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied. Required role(s): {', '.join(allowed_roles)}. "
                    f"Your role: {role or 'none'}."
                ),
            )

        return payload

    return _enforce


# ------------------------------------------------------------
# ADDED: Permission-based RBAC enforcement (enterprise model)
# ------------------------------------------------------------

def require_permission(permission: str):
    """
    Dependency factory that enforces permission-level RBAC
    using the policy.yaml configuration.

    Example:
        Depends(require_permission("view_all_logs"))
    """

    async def _enforce(
        credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    ) -> dict:

        # ------------------------------------------------------------------
        # 1. Ensure a token is provided
        # ------------------------------------------------------------------
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Provide a Bearer token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # ------------------------------------------------------------------
        # 2. Verify JWT
        # ------------------------------------------------------------------
        try:
            payload = verify_token(credentials.credentials)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        role = payload.get("role")

        # ------------------------------------------------------------------
        # 3. Load permissions for the role from policy.yaml
        # ------------------------------------------------------------------
        permissions = get_role_permissions(role)

        # ------------------------------------------------------------------
        # 4. Admin override
        # ------------------------------------------------------------------
        if "access_all_endpoints" in permissions:
            return payload

        # ------------------------------------------------------------------
        # 5. Enforce permission
        # ------------------------------------------------------------------
        if permission not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' denied for role '{role}'",
            )

        return payload

    return _enforce
