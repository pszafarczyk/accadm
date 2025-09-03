from typing import Protocol

from password_admin.auth import LoginCredentials
from password_admin.auth import NewCredentials


class DbConnectionInterface(Protocol):
    """Interface for database connection."""

    def login(self, credentials: LoginCredentials) -> None:
        """Establishes connection to database.

        Should raise DbConnectionError/DbLoginError on failure.
        """

    def logout(self) -> None: ...

    def get_users(self) -> list[str]: ...

    def set_password(self, credentials: NewCredentials) -> None: ...
