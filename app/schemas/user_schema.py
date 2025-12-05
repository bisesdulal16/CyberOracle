from pydantic import BaseModel, Field, validator
import re


class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=8, max_length=50)

    @validator("username")
    def username_valid(cls, v):
        # Allow letters, numbers, underscores only
        if not re.match(r"^\w+$", v):
            raise ValueError(
                "Username can only contain letters, numbers, and underscores"
            )
        return v

    @validator("password")
    def password_secure(cls, v):
        # Ensure password contains at least one number and one letter
        if not re.match(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@#$%^&+=]{8,}$", v):
            raise ValueError(
                "Password must contain at least one letter, one number, and be 8+ chars"
            )
        return v
