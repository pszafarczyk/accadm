from typing import Annotated
from typing import Literal

from pydantic import PositiveInt
from pydantic import StringConstraints
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    database_type: Literal['postgres', 'ldap'] = 'postgres'
    database_address: str = 'localhost'
    database_port: int = 5432
    database_name: str | None = None
    base_dn: str | None = None
    max_username_length: PositiveInt = 256
    username_allowed_characters: Annotated[str, StringConstraints(min_length=1)] = 'a-zA-Z0-9_.-@'
    min_password_length: PositiveInt = 16
    max_password_length: PositiveInt = 256
    session_id_length: PositiveInt = 64
    session_duration_seconds: PositiveInt = 900
    max_sessions: PositiveInt = 1024


settings = Settings()
