from typing import Annotated
from typing import Literal

from pydantic import BaseModel
from pydantic import PositiveInt
from pydantic import StringConstraints
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class SessionConfig(BaseModel):
    """Settings related to sessions."""

    id_length: PositiveInt = 64
    duration_seconds: PositiveInt = 900
    max_amount: PositiveInt = 1024


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_nested_delimiter='__')

    database_type: Literal['postgres', 'ldap'] = 'postgres'
    session: SessionConfig = SessionConfig()
    max_username_length: PositiveInt = 256
    username_allowed_characters: Annotated[str, StringConstraints(min_length=1)] = 'a-zA-Z0-9_.-@'
    min_password_length: PositiveInt = 16
    max_password_length: PositiveInt = 256


settings = Settings()
