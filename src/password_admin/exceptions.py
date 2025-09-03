from fastapi import HTTPException
from fastapi import status


class BaseError(HTTPException):
    """Base class for all custom exceptions in the application."""


class DatabaseError(BaseError):
    """Base class for database-related errors."""


class DatabaseConnectionError(DatabaseError):
    """Raised when a database connection cannot be established."""

    def __init__(self, status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail: str = 'Communication error') -> None:
        super().__init__(status_code=status_code, detail=detail)


class DatabaseQueryError(DatabaseError):
    """Raised when a database query failed."""

    def __init__(self, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail: str = 'Internal error') -> None:
        super().__init__(status_code=status_code, detail=detail)


class DatabaseLoginError(DatabaseError):
    """Raised when authentication with the database fails."""

    def __init__(self, username: str, detail: str = 'Login failed') -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"{detail} for user '{username}'")


class SessionNotFoundError(BaseError):
    """Raised when requested session does not exist (possibly expired)."""

    def __init__(self, detail: str = 'Session not found') -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)
