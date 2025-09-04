from password_admin.database.config import DbConfig
from password_admin.database.interface import DbConnectionInterface


class DbConnectionFactory:
    """DatabaseFactory stub."""

    def __init__(self, config: DbConfig):
        self.__config = config

    def create(self) -> DbConnectionInterface:  # type: ignore[empty-body]
        ...
