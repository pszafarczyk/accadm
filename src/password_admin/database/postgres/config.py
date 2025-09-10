from typing import Annotated

from pydantic import Field
from pydantic import field_validator
from pydantic import PostgresDsn
from pydantic import StringConstraints

from password_admin.database.config import DbConfig


class PostgresConfig(DbConfig):
    """Postgres related settings."""

    dsn: Annotated[PostgresDsn, Field(description='Postgres connection string with no user/password')] = PostgresDsn(
        'postgres://localhost:5432/postgres&sslmode=require'
    )
    users_query: Annotated[str, StringConstraints(min_length=1)] = 'SELECT username FROM users'
    password_query: Annotated[str, StringConstraints(min_length=1)] = 'UPDATE users SET password = %p WHERE username = %u'  # noqa: S105

    @field_validator('dsn')
    @classmethod
    def validate_dsn(cls, value: PostgresDsn) -> PostgresDsn:
        # Raise if username and password provided
        # Raise if db name not provided
        # Raise if host not valid
        # Raise if port not a number
        return value
