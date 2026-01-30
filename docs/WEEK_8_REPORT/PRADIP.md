# 🔐 CyberOracle — PSFR7 DB Encryption & Key Management Report

**Contributor:** Pradip Sapkota  
**Requirement ID:** PSFR7  
**Description:** Support DB encryption & key management  
**Date:** _(fill in)_

---

## 🎯 Objective

PSFR7 from the proposal:

> **“Support DB encryption & key management.”**  
> Output: *Encrypted Postgres DB using pgcrypto + key rotation in Vault.*

For Capstone I, the focus is on:

- Adding **application-level encryption** for sensitive values before they are stored.
- Managing encryption via **environment-based keys** (key + key ID).
- Ensuring the design can later plug into **Vault/KMS** or Postgres-native crypto,
  without breaking existing code or tests.

The implementation is intentionally **non-breaking**: when encryption is disabled,
CyberOracle behaves exactly as before.

---

## 🧠 Work Completed

### 1️⃣ Environment-Based Encryption Configuration

Updated `.env.example` with PSFR7 settings:

```env
# PSFR7 — Database Encryption & Key Management
DB_ENCRYPTION_ENABLED=false

# Symmetric encryption key (Fernet). For a real demo:
#   from cryptography.fernet import Fernet
#   print(Fernet.generate_key().decode())
# and paste that value here.
DB_ENCRYPTION_KEY=REPLACE_WITH_REAL_FERNET_KEY

# Logical key version (for future rotation, e.g. v1, v2...)
DB_ENCRYPTION_KEY_ID=v1
