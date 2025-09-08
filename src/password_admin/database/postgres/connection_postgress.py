import logging
import psycopg2
from psycopg2 import OperationalError, ProgrammingError
from password_admin.auth import LoginCredentials, NewCredentials
from password_admin.database.postgres.config import PostgresConfig
import password_admin.exceptions


class DatabaseConnectionPostgres:
    """Manages connections and operations with a PostgreSQL database.

    Provides methods to configure, connect, query, and modify data in a PostgreSQL database using the psycopg2 library.
    Supports user authentication, retrieval of user identifiers, and password updates. Logs operations and errors
    using the Python logging module.

    Attributes:
        connection (psycopg2.connection): The active connection to the PostgreSQL database.
        cursor (psycopg2.cursor): The cursor for executing database queries.
        config_data (PostgresConfig): Configuration data for the database connection.
        logger (logging.Logger): Logger instance for recording operations and errors.
    """

    def __init__(self, config: PostgresConfig):
        """Initializes the PostgreSQL connection attributes.

        Sets up the initial state with no connection or cursor established. The `config` method is called
        with the provided configuration to prepare the database connection. Initializes the logger.

        Args:
            config (PostgresConfig): Configuration object containing database connection details (e.g., DSN).
        """
        self.connection = None
        self.cursor = None
        self.config_data: PostgresConfig
        self.logger = logging.getLogger(__name__)
        self.config(config)

    def config(self, config: PostgresConfig) -> None:
        """Configures the PostgreSQL database connection parameters.

        Stores the provided configuration for use in establishing a database connection.

        Args:
            config (PostgresConfig): Configuration object containing database connection details.

        Raises:
            password_admin.exceptions.DbConnectionError: If the configuration fails due to invalid parameters.
            AttributeError: If the configuration object is invalid (e.g., missing DSN).
        """
        try:
            self.config_data = config
            self.logger.info('Configured PostgreSQL database connection parameters')
        except AttributeError as e:
            self.logger.error(f'Configuration error: Invalid configuration: {e}')
            raise password_admin.exceptions.DbConnectionError(detail=f'Configuration error: Invalid configuration: {str(e)}')

    def login(self, credentials: LoginCredentials) -> None:
        """Establishes a connection to the PostgreSQL database.

        Connects to the database using the provided credentials and configuration. Creates a cursor for
        executing queries. The configuration must be set using `config` before calling this method.

        Args:
            credentials (LoginCredentials): Object containing the username and password for authentication.

        Raises:
            password_admin.exceptions.DbLoginError: If the connection fails (e.g., invalid credentials or database unreachable).
        """
        try:
            self.connection = psycopg2.connect(
                dsn=str(self.config_data.dsn),
                user=credentials.username,
                password=credentials.password,
            )
            self.cursor = self.connection.cursor()
            self.logger.info('Successfully connected to PostgreSQL database')
        except OperationalError as e:
            self.logger.error(f"Login error for user '{credentials.username}': {e}")
            raise password_admin.exceptions.DbLoginError(username=credentials.username, detail=f'Login error: {str(e)}')

    def get_users(self) -> list[str]:
        """Retrieves a list of user identifiers from the PostgreSQL database.

        Executes the configured query to fetch user identifiers from the specified table.
        Assumes the query returns a single column of user identifiers.

        Returns:
            list[str]: A list of user identifiers (e.g., usernames). Returns an empty list if no users
                are found or an error occurs.

        Raises:
            password_admin.exceptions.DbConnectionError: If no connection or cursor is established (i.e., `login` was not called).
            password_admin.exceptions.DbQueryError: If the query execution fails (e.g., invalid query or database issues).
        """
        try:
            if not self.connection or not self.cursor:
                self.logger.error('Not connected. Call login() first.')
                raise password_admin.exceptions.DbConnectionError(detail='Not connected. Call login() first.')

            query = self.config_data.users_query
            self.cursor.execute(query)
            rows = self.cursor.fetchall()

            users = [row[0] for row in rows]
            self.logger.info(f'Retrieved {len(users)} users from PostgreSQL database')
            return users

        except ProgrammingError as e:
            self.logger.error(f'Error retrieving users: {e}')
            raise password_admin.exceptions.DbQueryError(detail=f'Error retrieving users: {str(e)}')
        except ValueError as e:
            self.logger.error(f'Error retrieving users: {e}')
            raise password_admin.exceptions.DbConnectionError(detail=f'Error retrieving users: {str(e)}')

    def set_password(self, credentials: NewCredentials) -> None:
        """Updates a user's password in the PostgreSQL database.

        Executes the configured query to update the password for the specified user.
        Commits the transaction if successful.

        Args:
            new_credentials (NewCredentials): Object containing the username and new password.

        Returns:
            bool: True if the password update is successful, False if no rows are affected or an error occurs.

        Raises:
            password_admin.exceptions.DbConnectionError: If no connection or cursor is established (i.e., `login` was not called).
            password_admin.exceptions.DbQueryError: If the query execution fails (e.g., invalid query or database issues).
            password_admin.exceptions.SessionNotFoundError: If no user is found with the specified identifier.
        """
        try:
            if not self.connection or not self.cursor:
                self.logger.error('Not connected. Call login() first.')
                raise password_admin.exceptions.DbConnectionError(detail='Not connected. Call login() first.')

            query = self.config_data.password_query
            query = query.replace('%p', '%s').replace('%u', '%s')

            self.cursor.execute(query, (credentials.password, credentials.username))
            self.connection.commit()

            success = self.cursor.rowcount > 0
            if success:
                self.logger.info(f'Successfully updated password for user: {credentials.username}')
            else:
                self.logger.warning(f'No user found with identifier: {credentials.username}')
                raise password_admin.exceptions.SessionNotFoundError(detail=f'No user found with identifier: {credentials.username}')

        except ProgrammingError as e:
            self.logger.error(f'Error updating password: {e}')
            raise password_admin.exceptions.DbQueryError(detail=f'Error updating password: {str(e)}')
        except (password_admin.exceptions.DbConnectionError, password_admin.exceptions.SessionNotFoundError):
            raise
        except ValueError as e:
            self.logger.error(f'Error updating password: {e}')
            raise password_admin.exceptions.DbConnectionError(detail=f'Error updating password: {str(e)}')

    def logout(self) -> None:
        """Closes the connection to the PostgreSQL database.

        Closes the cursor and connection, releasing database resources.

        Raises:
            password_admin.exceptions.DbConnectionError: If closing the connection or cursor fails (e.g., database issues).
        """
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
                self.logger.info('Successfully disconnected from PostgreSQL database')
                self.connection = None
                self.cursor = None
            else:
                self.logger.info('Logout not needed')
        except OperationalError as e:
            self.logger.error(f'Logout error: {e}')
            raise password_admin.exceptions.DbConnectionError(detail=f'Logout error: {str(e)}')
