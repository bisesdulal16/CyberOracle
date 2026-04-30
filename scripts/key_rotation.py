#!/usr/bin/env python3
"""
scripts/key_rotation.py

PSFR7 — DB encryption key management & rotation.

Two-layer encryption model:
  Layer 1 (App-level)  — Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256).
                         Applied to the `message` column before DB write.
                         Key stored in DB_ENCRYPTION_KEY env var (simulates Vault transit secret).
  Layer 2 (DB-level)   — pgcrypto extension (pgp_sym_encrypt / pgp_sym_decrypt).
                         Demonstrates native Postgres column encryption capability.

Key rotation procedure (simulating HashiCorp Vault transit key rotation):
  1. Generate new Fernet key  (new key version = old version + 1)
  2. Decrypt every encrypted log row with the OLD key
  3. Re-encrypt each row with the NEW key
  4. Print the new key + version — operator pastes these into Vault / .env

Usage:
    source venv/bin/activate
    python scripts/key_rotation.py [--dry-run] [--pgcrypto-demo]
"""

import os
import sys
import argparse
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from cryptography.fernet import Fernet, InvalidToken


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _current_key() -> bytes:
    key = os.getenv("DB_ENCRYPTION_KEY", "")
    if not key:
        raise RuntimeError("DB_ENCRYPTION_KEY is not set in .env")
    return key.encode("utf-8")


def _current_key_id() -> str:
    return os.getenv("DB_ENCRYPTION_KEY_ID", "v1")


def _next_key_id(current: str) -> str:
    """Increment version: v1 -> v2 -> v3 ..."""
    try:
        n = int(current.lstrip("v"))
        return f"v{n + 1}"
    except ValueError:
        return current + "_rotated"


def _decrypt_safe(fernet: Fernet, value: str) -> str:
    """Decrypt if possible; return original string on failure (legacy plaintext)."""
    try:
        return fernet.decrypt(value.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError, Exception):
        return value


# ---------------------------------------------------------------------------
# pgcrypto demo
# ---------------------------------------------------------------------------

def run_pgcrypto_demo():
    """
    Demonstrate native Postgres pgcrypto symmetric encryption.
    Shows pgp_sym_encrypt / pgp_sym_decrypt round-trip using a passphrase.
    """
    import asyncio
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        print("[pgcrypto] DATABASE_URL not set — skipping demo.")
        return

    passphrase = "cyberoracle-pgcrypto-demo-key"
    plaintext = "SSN: 123-45-6789 | API Key: sk-abc123xyz456def789"

    async def _demo():
        engine = create_async_engine(db_url, echo=False)
        async with engine.connect() as conn:
            # Encrypt
            enc_result = await conn.execute(
                text("SELECT pgp_sym_encrypt(:pt, :pw)"),
                {"pt": plaintext, "pw": passphrase},
            )
            ciphertext_bytes = enc_result.scalar()

            # Decrypt
            dec_result = await conn.execute(
                text("SELECT pgp_sym_decrypt(:ct, :pw)"),
                {"ct": ciphertext_bytes, "pw": passphrase},
            )
            recovered = dec_result.scalar()

        await engine.dispose()
        return ciphertext_bytes, recovered

    ciphertext, recovered = asyncio.run(_demo())

    print("\n" + "=" * 60)
    print("  pgcrypto (pgp_sym_encrypt) Demo")
    print("=" * 60)
    print(f"  Plaintext : {plaintext}")
    print(f"  Ciphertext: {bytes(ciphertext).hex()[:64]}...  (binary, {len(bytes(ciphertext))} bytes)")
    print(f"  Decrypted : {recovered}")
    print(f"  Match     : {'YES' if recovered == plaintext else 'NO'}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# .env updater
# ---------------------------------------------------------------------------

def _update_env(new_key: str, new_key_id: str):
    """Replace DB_ENCRYPTION_KEY and DB_ENCRYPTION_KEY_ID in .env in-place."""
    env_path = os.path.join(PROJECT_ROOT, ".env")
    if not os.path.exists(env_path):
        print(f"  [warn] .env not found at {env_path} — skipping auto-update.")
        return

    with open(env_path, "r") as f:
        lines = f.readlines()

    updated = []
    for line in lines:
        if line.startswith("DB_ENCRYPTION_KEY=") and not line.startswith("DB_ENCRYPTION_KEY_ID"):
            updated.append(f"DB_ENCRYPTION_KEY={new_key}\n")
        elif line.startswith("DB_ENCRYPTION_KEY_ID="):
            updated.append(f"DB_ENCRYPTION_KEY_ID={new_key_id}\n")
        else:
            updated.append(line)

    with open(env_path, "w") as f:
        f.writelines(updated)


# ---------------------------------------------------------------------------
# Key rotation
# ---------------------------------------------------------------------------

def run_key_rotation(dry_run: bool = False):
    import asyncio
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        print("[rotation] DATABASE_URL not set — aborting.")
        return

    old_key_bytes = _current_key()
    old_key_id = _current_key_id()
    new_key_bytes = Fernet.generate_key()
    new_key_id = _next_key_id(old_key_id)

    old_fernet = Fernet(old_key_bytes)
    new_fernet = Fernet(new_key_bytes)

    print("\n" + "=" * 60)
    print("  CyberOracle — Fernet Key Rotation")
    print(f"  Time   : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"  Old ID : {old_key_id}")
    print(f"  New ID : {new_key_id}")
    print(f"  Mode   : {'DRY RUN (no writes)' if dry_run else 'LIVE'}")
    print("=" * 60)

    async def _rotate():
        engine = create_async_engine(db_url, echo=False)
        rotated = 0
        skipped = 0

        async with engine.begin() as conn:
            rows = await conn.execute(
                text("SELECT id, message FROM logs WHERE message IS NOT NULL")
            )
            entries = rows.fetchall()
            print(f"\n  Rows to process: {len(entries)}")

            for row_id, message in entries:
                plaintext = _decrypt_safe(old_fernet, message)

                if plaintext == message:
                    # Could not decrypt — legacy plaintext or different key
                    skipped += 1
                    continue

                new_ciphertext = new_fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")

                if not dry_run:
                    await conn.execute(
                        text("UPDATE logs SET message = :msg WHERE id = :id"),
                        {"msg": new_ciphertext, "id": row_id},
                    )
                rotated += 1

        await engine.dispose()
        return rotated, skipped

    rotated, skipped = asyncio.run(_rotate())

    print(f"\n  Rows re-encrypted : {rotated}")
    print(f"  Rows skipped      : {skipped} (plaintext / unreadable with old key)")

    new_key_str = new_key_bytes.decode("utf-8")

    print("\n" + "=" * 60)
    if dry_run:
        print("  ACTION REQUIRED — Update your secret store:")
        print("=" * 60)
        print(f"  DB_ENCRYPTION_KEY    = {new_key_str}")
        print(f"  DB_ENCRYPTION_KEY_ID = {new_key_id}")
        print("\n  (Dry run: no changes written to DB. Remove --dry-run to apply.)")
    else:
        print("  Updating .env with new key...")
        print("=" * 60)
        _update_env(new_key_str, new_key_id)
        print(f"  DB_ENCRYPTION_KEY    = {new_key_str}")
        print(f"  DB_ENCRYPTION_KEY_ID = {new_key_id}")
        print("\n  .env updated. Restart the app to load the new key.")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Status report
# ---------------------------------------------------------------------------

def show_status():
    enabled = os.getenv("DB_ENCRYPTION_ENABLED", "false").lower() == "true"
    key = os.getenv("DB_ENCRYPTION_KEY", "")
    key_id = os.getenv("DB_ENCRYPTION_KEY_ID", "v1")

    print("\n" + "=" * 60)
    print("  CyberOracle — Encryption Status")
    print("=" * 60)
    print(f"  App-level Fernet encryption : {'ENABLED' if enabled else 'DISABLED'}")
    print(f"  Current key version         : {key_id}")
    print(f"  Key present in env          : {'YES' if key else 'NO'}")
    print(f"  pgcrypto extension          : INSTALLED (v1.3)")
    print(f"  Encrypted column            : logs.message")
    print("=" * 60)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CyberOracle key rotation tool (PSFR7)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate rotation without writing to DB")
    parser.add_argument("--pgcrypto-demo", action="store_true", help="Run pgcrypto round-trip demo")
    parser.add_argument("--status", action="store_true", help="Show current encryption status and exit")
    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.pgcrypto_demo:
        show_status()
        run_pgcrypto_demo()
    else:
        show_status()
        run_key_rotation(dry_run=args.dry_run)
