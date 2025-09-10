import logging

from password_admin.database.config import DbConfig
from password_admin.database.interface import DbConnectionInterface
from password_admin.database.ldap.config import LdapConfig
from password_admin.database.ldap.connection import DatabaseConnectionLdap
from password_admin.database.postgres.config import PostgresConfig
from password_admin.database.postgres.connection import DatabaseConnectionPostgres
import password_admin.exceptions


class DbConnectionFactory:
    """Factory for creating database connection instances based on configuration.

    Creates instances of database connection classes (e.g., LDAP or PostgreSQL) based
    on the provided configuration type. Logs operations and errors using the Python
    logging module.

    Attributes:
        __config (DbConfig): The configuration object for the database connection.
        logger (logging.Logger): Logger instance for recording operations and errors.
    """

    def __init__(self, config: DbConfig):
        """Initializes the factory with a database configuration.

        Args:
            config (DbConfig): Configuration object for the database (e.g.,
                LdapConfig or PostgresConfig).
        """
        self.__config = config
        self.logger = logging.getLogger(__name__)
        self.logger.info('Initialized DbConnectionFactory with config type: %s', type(config).__name__)

    def create(self) -> DbConnectionInterface:
        """Creates a database connection instance based on the configuration.

        Returns:
            DbConnectionInterface: An instance of a database connection class (e.g.,
                DatabaseConnectionLdap or DatabaseConnectionPostgres).

        Raises:
            password_admin.exceptions.DbConnectionError: If the configuration type is
                unsupported or connection creation fails.
            AttributeError: If the configuration object is invalid (e.g., missing
                required attributes).
        """
        try:
            if isinstance(self.__config, LdapConfig):
                self.logger.info('Creating LDAP database connection')
                return DatabaseConnectionLdap(self.__config)
            if isinstance(self.__config, PostgresConfig):
                self.logger.info('Creating PostgreSQL database connection')
                return DatabaseConnectionPostgres(self.__config)
            self.logger.error('Unsupported config type: %s', type(self.__config).__name__)
            raise password_admin.exceptions.DbConnectionError(detail=f'Unsupported config type: {type(self.__config).__name__}')
        except AttributeError as e:
            self.logger.exception('Invalid configuration')
            raise password_admin.exceptions.DbConnectionError(detail=f'Invalid configuration: {e!s}') from None
