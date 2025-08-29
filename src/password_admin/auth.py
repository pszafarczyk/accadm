import re
from typing import Annotated

from pydantic import BaseModel
from pydantic import field_validator
from pydantic import StringConstraints

from password_admin.settings import settings


class LoginCredentials(BaseModel):
    """Credentials used for logging in."""

    username: Annotated[str, StringConstraints(min_length=1, max_length=settings.max_username_length, pattern=f'^[{settings.username_allowed_characters}]+$')]
    password: Annotated[str, StringConstraints(min_length=settings.min_password_length, max_length=settings.max_password_length)]


class NewCredentials(LoginCredentials):
    """Credentials used when setting a new password."""

    @field_validator('password')
    def validate_password(self, value: str) -> str:
        msg = None
        if not re.search(r'[A-Za-z]', value):
            msg = 'Password must contain at least one letter'
        if not re.search(r'\d', value):
            msg = 'Password must contain at least one number'
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            msg = 'Password must contain at least one special character'
        if msg:
            raise ValueError(msg)
        return value
