from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    Truncate to 72 bytes to satisfy bcrypt limitation.
    """
    return pwd_context.hash(password[:72])

# Example users
users_db = {
    "alice": {"username": "alice", "password": hash_password("alice123"), "role": "admin"},
    "bob": {"username": "bob", "password": hash_password("bob123"), "role": "user"},
}

def authenticate_user(username: str, password: str):
    user = users_db.get(username)
    if not user:
        return None
    # Truncate input password as well (to match hashing behavior)
    if not pwd_context.verify(password[:72], user["password"]):
        return None
    return user
