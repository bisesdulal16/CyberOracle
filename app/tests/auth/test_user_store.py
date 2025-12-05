from app.auth.user_store import (
    hash_password,
    authenticate_user,
    create_user,
    pwd_context,
)


# ---------------------------------------------------------
# TEST 1 — bcrypt truncation handling (correct behavior)
# ---------------------------------------------------------
def test_hash_password_truncates_to_72_bytes():
    long_password = "A" * 200  # way beyond bcrypt's limit
    hashed = hash_password(long_password)

    # bcrypt truncates to 72 characters when hashing
    assert pwd_context.verify("A" * 72, hashed)

    # bcrypt ALSO truncates inputs during verification
    assert pwd_context.verify("A" * 200, hashed)

    # A different truncated value must NOT verify
    assert not pwd_context.verify("B" * 72, hashed)


# ---------------------------------------------------------
# TEST 2 — authenticate_user success
# ---------------------------------------------------------
def test_authenticate_user_success():
    username = "testuser1"
    password = "StrongPass123!"

    # create the user
    create_user(username, password)

    # authentication should succeed
    user = authenticate_user(username, password)
    assert user is not None
    assert user["username"] == username


# ---------------------------------------------------------
# TEST 3 — authenticate_user fails for wrong password
# ---------------------------------------------------------
def test_authenticate_user_wrong_password():
    username = "testuser2"
    password = "CorrectPass123!"

    create_user(username, password)

    # wrong password should fail
    assert authenticate_user(username, "WrongPassword!") is None


# ---------------------------------------------------------
# TEST 4 — authenticate_user fails for nonexistent user
# ---------------------------------------------------------
def test_authenticate_user_no_user():
    assert authenticate_user("nonexistent_user", "anything123") is None


# ---------------------------------------------------------
# TEST 5 — create_user prevents duplicate usernames
# ---------------------------------------------------------
def test_create_user_duplicate():
    username = "uniqueuser"
    password = "SomePass99!"

    created = create_user(username, password)
    assert created is not None  # first time OK

    duplicate = create_user(username, password)
    assert duplicate is None  # duplicates must be blocked


# ---------------------------------------------------------
# TEST 6 — password hashing produces unique hashes even for identical passwords
# ---------------------------------------------------------
def test_hash_password_creates_unique_hashes():
    pwd = "SamePassword123!"

    hash1 = hash_password(pwd)
    hash2 = hash_password(pwd)

    # bcrypt salts => they must be different
    assert hash1 != hash2

    # but both must verify correctly
    assert pwd_context.verify(pwd, hash1)
    assert pwd_context.verify(pwd, hash2)
