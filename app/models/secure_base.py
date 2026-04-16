import re
from pydantic import BaseModel, field_validator

# Global forbidden patterns
FORBIDDEN_PATTERNS = [
    r";",
    r"--",
    r"\/\*",
    r"\*\/",
    r"<script>",
    r"</script>",
    r"SELECT\s",
    r"DROP\s",
    r"INSERT\s",
    r"DELETE\s",
    r"UPDATE\s",
]


def contains_malicious_pattern(value: str) -> bool:
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            return True
    return False


class SecureBaseModel(BaseModel):
    """
    Global secure base model.

    All request models should inherit from this.
    Provides automatic:
    - String trimming
    - Injection detection
    """

    @field_validator("*", mode="before")
    @classmethod
    def sanitize_all_strings(cls, value):

        if isinstance(value, str):
            value = value.strip()

            if contains_malicious_pattern(value):
                raise ValueError("Input contains unsafe or malicious patterns.")

            return value

        return value
