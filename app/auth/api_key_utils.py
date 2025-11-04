import hashlib

VALID_API_KEYS = set()

def generate_api_key(user: str) -> str:
    key = hashlib.sha256(user.encode()).hexdigest()
    VALID_API_KEYS.add(key)
    return key

def validate_api_key(key: str) -> bool:
    return key in VALID_API_KEYS
