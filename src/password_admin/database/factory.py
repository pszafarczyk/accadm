from password_admin.database.config import DbConfig
from password_admin.database.interface import DbConnectionInterface
from .database_connection_ldap import DatabaseConnectionLdap, LdapConfig
from .database_connection_postgress import DatabaseConnectionPostgres, PostgreConfig


class DbConnectionFactory:
    """DatabaseFactory stub."""

    def __init__(self, config: DbConfig):
        self.__config = config

    def create(self) -> DbConnectionInterface:  # type: ignore[empty-body]
        if isinstance(self.__config, LdapConfig):
            database_connection = DatabaseConnectionLdap(self.__config)
            return database_connection
        elif type(self.__config) is PostgreConfig:
            database_connection = DatabaseConnectionPostgres(self.__config)
            return database_connection
        else:
            raise ValueError(f'Unsupported config type: {type(self.__config)}')
