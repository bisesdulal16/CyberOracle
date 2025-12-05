from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    Truncate to 72 bytes to satisfy bcrypt limitation.
    """
    return pwd_context.hash(password[:72])


# In-memory user database
users_db = {
    "alice": {
        "username": "alice",
        "password": hash_password("Alice_123"),
        "role": "admin",
    },
    "bob": {"username": "bob", "password": hash_password("Bob_1234"), "role": "user"},
}


def authenticate_user(username: str, password: str):
    user = users_db.get(username)
    if not user:
        return None
    if not pwd_context.verify(password[:72], user["password"]):
        return None
    return user


def create_user(username: str, password: str, role: str = "user"):
    """
    Create a new user. Default role = user.
    """
    if username in users_db:
        return None  # Already exists

    users_db[username] = {
        "username": username,
        "password": hash_password(password),
        "role": role,
    }
    return users_db[username]
