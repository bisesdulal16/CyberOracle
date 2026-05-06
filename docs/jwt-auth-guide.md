# JWT Authentication Guide

## Overview

CyberOracle uses **JSON Web Tokens (JWT)** to authenticate users and enforce role-based access control (RBAC) on every protected endpoint. Tokens are signed with HMAC-SHA256 (HS256) and expire after **30 minutes**.

---

## Authentication Flow

```
Client                          CyberOracle API
  │                                    │
  │  POST /auth/login                  │
  │  { "username": "...",              │
  │    "password": "..." }  ──────────>│
  │                                    │  1. Lookup user in store
  │                                    │  2. bcrypt.verify(password, stored_hash)
  │                                    │  3. create_access_token({ sub, role })
  │  { access_token, role } <──────────│
  │                                    │
  │  GET /some/protected               │
  │  Authorization: Bearer <token> ───>│
  │                                    │  4. HTTPBearer extracts token
  │                                    │  5. jwt.decode(token, SECRET_KEY, HS256)
  │                                    │  6. Validate sub + role claims
  │                                    │  7. Check role / permission policy
  │  200 OK (or 401/403)  <────────────│
```

---

## Token Structure

Every issued JWT contains three standard parts: `header.payload.signature`.

### Header
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

### Payload (Claims)
| Claim | Type     | Description                              |
|-------|----------|------------------------------------------|
| `sub` | string   | Username (subject)                       |
| `role`| string   | User role — `admin`, `developer`, or `auditor` |
| `exp` | timestamp| Expiry — 30 minutes from issue time      |
| `iat` | timestamp| Issued-at — UTC timestamp of creation    |

Example decoded payload:
```json
{
  "sub": "admin",
  "role": "admin",
  "exp": 1714000000,
  "iat": 1713998200
}
```

### Signature
```
HMAC-SHA256(base64url(header) + "." + base64url(payload), JWT_SECRET_KEY)
```
The secret is read from the `JWT_SECRET_KEY` environment variable. It falls back to `"dev_only_secret_change_in_prod"` if unset — **never use the default in production**.

---

## Login Endpoint

**`POST /auth/login`**

Request:
```json
{
  "username": "admin",
  "password": "changeme_admin"
}
```

Response:
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "role": "admin"
}
```

Credentials are resolved in this order:
1. `ADMIN_USERNAME` / `ADMIN_PASSWORD_HASH` env vars
2. `DEV_USERNAME` / `DEV_PASSWORD_HASH` env vars
3. `AUDITOR_USERNAME` / `AUDITOR_PASSWORD_HASH` env vars
4. Hardcoded bcrypt defaults (dev only)

Passwords are **never stored or compared in plaintext** — only the bcrypt hash is stored. Even for unknown usernames, bcrypt verification still runs to prevent user enumeration via timing attacks (OWASP API2).

---

## Using the Token

Include the token in the `Authorization` header of every protected request:

```
Authorization: Bearer <access_token>
```

Example with curl:
```bash
TOKEN=$(curl -s -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"changeme_admin"}' | jq -r '.access_token')

curl -H "Authorization: Bearer $TOKEN" http://localhost:8001/auth/me
```

---

## RBAC Enforcement

There are two enforcement layers, both implemented as FastAPI dependency factories.

### 1. `require_roles(*allowed_roles)` — Role-Based

Checks that the `role` claim in the token matches one of the explicitly listed roles.

```python
@router.get("/admin-only")
async def endpoint(user=Depends(require_roles("admin"))):
    ...
```

Used when an endpoint should be accessible only to specific roles regardless of fine-grained permissions.

### 2. `require_permission(permission)` — Permission-Based

Looks up the role's permissions from `docs/threat-modeling/policy.yaml` and checks whether the required permission is present.

```python
@router.post("/ai/query")
async def query(user=Depends(require_permission("test_api_endpoints"))):
    ...
```

**Admin override:** if a role has `access_all_endpoints` in its permission list, the check passes unconditionally.

---

## Roles and Permissions

Defined in [`docs/threat-modeling/policy.yaml`](threat-modeling/policy.yaml).

| Role        | Key Permissions                                                                 | Rate Limit     |
|-------------|---------------------------------------------------------------------------------|----------------|
| `admin`     | `manage_users`, `modify_policies`, `view_all_logs`, `access_all_endpoints`, ... | 1000 req/min   |
| `developer` | `test_api_endpoints`, `view_own_logs`, `read_dlp_rules`, `view_dashboards`      | 100 req/min    |
| `auditor`   | `view_all_logs`, `generate_compliance_reports`, `export_audit_trails`, ...      | 50 req/min     |

---

## Error Responses

| HTTP Code | Cause                                              |
|-----------|----------------------------------------------------|
| `401`     | Missing `Authorization` header or malformed token  |
| `401`     | Token expired or signature invalid                 |
| `401`     | Token missing `sub` or `role` claim                |
| `403`     | Valid token but role not in `allowed_roles`        |
| `403`     | Valid token but role lacks the required permission |

---

## Token Verification Logic (`verify_token`)

```
jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
  └─ checks signature
  └─ checks exp (raises JWTError if expired)
  └─ checks sub claim present
  └─ checks role claim present
```

Any `JWTError` from the library (bad signature, expired, malformed) is caught and re-raised as a plain `ValueError` so no JWT internals leak to the caller.

---

## Additional Endpoints

| Endpoint              | Method | Auth Required         | Description                        |
|-----------------------|--------|-----------------------|------------------------------------|
| `/auth/login`         | POST   | None                  | Exchange credentials for a token   |
| `/auth/me`            | GET    | Any valid role        | Returns `{ username, role }`       |
| `/auth/apikey/generate` | POST | `admin` only          | Generate a machine-to-machine key  |

---

## Security Notes

- Tokens expire in **30 minutes** — there is no refresh token endpoint; clients must re-login.
- The `JWT_SECRET_KEY` must be a strong random value in production (min 32 bytes hex).
- Algorithm is pinned to `HS256` — the `algorithms` parameter in `jwt.decode` prevents algorithm-confusion attacks.
- The `HTTPBearer` extractor is set to `auto_error=False` in RBAC so that custom 401 messages are returned instead of FastAPI's default.
