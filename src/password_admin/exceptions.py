class BaseError(Exception):
    """Base class for all custom exceptions in the application."""


class DatabaseError(BaseError):
    """Base class for database-related errors."""


class DatabaseConnectionError(DatabaseError):
    """Raised when a database connection cannot be established."""


class DatabaseLoginError(DatabaseError):
    """Raised when authentication with the database fails."""

    def __init__(self, username: str, message: str = 'Database login failed') -> None:
        super().__init__(f"{message} for user '{username}'")


class SessionNotFoundError(BaseError):
    """Raised when requested session does not exist (possibly expired)."""

    def __init__(self, token: str, message: str = 'Session not found') -> None:
        super().__init__(f"{message} for token '{token}'")
