import logging
from ldap3 import Server, Connection, MODIFY_REPLACE, ALL
from ldap3.core.exceptions import LDAPException
from password_admin.auth import LoginCredentials, NewCredentials
from password_admin.database.ldap.config import LdapConfig
import urllib.parse
import password_admin.exceptions


class DatabaseConnectionLdap:
    """Manages connections and operations with an OpenLDAP server.

    Provides methods to configure, connect, query, and modify data on an LDAP server using the ldap3 library.
    Supports user authentication, retrieval of user attributes, and password updates. Logs operations and errors
    using the Python logging module.

    Attributes:
        server (ldap3.Server): The LDAP server object, initialized during configuration.
        connection (ldap3.Connection): The active connection to the LDAP server.
        config_data (LdapConfig): Configuration data for the LDAP server connection.
        logger (logging.Logger): Logger instance for recording operations and errors.
    """

    def __init__(self, config: LdapConfig):
        """Initializes the LDAP connection attributes.

        Sets up the initial state with no server or connection established. The `config` method is called
        with the provided configuration to prepare the server connection. Initializes the logger.

        Args:
            config (LdapConfig): Configuration object containing LDAP server details (e.g., host, port, base DN).
        """
        self.server = None
        self.connection = None
        self.config_data: LdapConfig
        self.logger = logging.getLogger(__name__)
        self.config(config)

    def config(self, config: LdapConfig) -> None:
        """Configures the LDAP server connection parameters.

        Sets up the LDAP server with the provided configuration, including host, port, and base DN.
        Prepares the server for connection but does not establish it.

        Args:
            config (LdapConfig): Configuration object containing LDAP server details.

        Raises:
            password_admin.exceptions.DbConnectionError: If the configuration is invalid (e.g., missing hostname in DSN).
            AttributeError: If DSN parsing fails due to invalid configuration.
        """
        try:
            self.config_data = config
            parsed = urllib.parse.urlparse(self.config_data.dsn)

            if parsed.hostname:
                self.server = Server(host=parsed.hostname, port=parsed.port, use_ssl=self.config_data.use_ssl, get_info=ALL)
                self.logger.info(f'Configured LDAP server: {parsed.hostname}:{parsed.port}')
            else:
                self.logger.error('Invalid DSN: Missing hostname')
                raise password_admin.exceptions.DbConnectionError(detail='Invalid DSN: Missing hostname')
        except AttributeError as e:
            self.logger.error(f'Configuration error: Invalid DSN format: {e}')
            raise password_admin.exceptions.DbConnectionError(detail=f'Configuration error: Invalid DSN format: {str(e)}')

    def login(self, credentials: LoginCredentials) -> None:
        """Establishes and binds a connection to the LDAP server.

        Authenticates to the LDAP server using the provided credentials. The server must be configured
        using `config` before calling this method.

        Args:
            credentials (LoginCredentials): Object containing the username and password for authentication.

        Raises:
            password_admin.exceptions.DbConnectionError: If the server is not configured (i.e., `config` was not called).
            password_admin.exceptions.DbLoginError: If authentication fails (e.g., invalid credentials or server unreachable).
        """
        try:
            if not self.server:
                self.logger.error('Server not configured. Call config() first.')
                raise password_admin.exceptions.DbConnectionError(detail='Server not configured. Call config() first.')
            self.connection = Connection(self.server, user=self._admin_parsing(credentials.username), password=credentials.password, auto_bind=True)
            self.logger.info('Successfully connected to LDAP server')
        except LDAPException as e:
            self.logger.error(f"Login error for user '{credentials.username}': {e}")
            raise password_admin.exceptions.DbLoginError(username=credentials.username, detail=f'Login error: {str(e)}')

    def _admin_parsing(self, admin_str: str) -> str:
        """Constructs the Distinguished Name (DN) for the admin user.

        Combines the provided admin username with the base bind DN from the configuration.

        Args:
            admin_str (str): The admin username (e.g., 'admin').

        Returns:
            str: The full Distinguished Name (e.g., 'cn=admin,dc=example,dc=com').
        """
        return 'cn=' + admin_str + ',' + self.config_data.base_bind_dn

    def get_users(self) -> list[str]:
        """Retrieves a list of user identifiers from the LDAP server.

        Queries the LDAP server for users matching the configured search filter and returns their
        name attributes as specified in the configuration.

        Returns:
            list[str]: A list of user identifiers (e.g., usernames). Returns an empty list if no users
                are found or an error occurs.

        Raises:
            password_admin.exceptions.DbConnectionError: If no connection is established or bound (i.e., `login` was not called).
            password_admin.exceptions.DbQueryError: If the search operation fails (e.g., invalid search filter or server issues).
        """
        try:
            if not self.connection or not self.connection.bound:
                self.logger.error('Not connected. Call login() first.')
                raise password_admin.exceptions.DbConnectionError(detail='Not connected. Call login() first.')

            self.connection.search(
                search_base=self.config_data.base_dn,
                search_filter=self.config_data.search_filter,
                attributes=[self.config_data.name_attribute],
            )

            users = []
            for entry in self.connection.entries:
                if self.config_data.name_attribute in entry:
                    users.append(entry[self.config_data.name_attribute].value)

            self.logger.info(f'Retrieved {len(users)} users from LDAP server')
            return users

        except LDAPException as e:
            self.logger.error(f'Error retrieving users: {e}')
            raise password_admin.exceptions.DbQueryError(detail=f'Error retrieving users: {str(e)}')

    def set_password(self, credentials: NewCredentials) -> None:
        """Updates the password for a user in the LDAP server.

        Modifies the password attribute for the specified user identified by their username.
        Uses the MODIFY_REPLACE operation to update the password.

        Args:
            new_credentials (NewCredentials): Object containing the username and new password.

        Raises:
            password_admin.exceptions.DbConnectionError: If no connection is established or bound (i.e., `login` was not called).
            password_admin.exceptions.SessionNotFoundError: If no user or multiple users are found for the given identifier.
            password_admin.exceptions.DbQueryError: If the modification operation fails (e.g., invalid password format or server issues).
        """
        try:
            if not self.connection or not self.connection.bound:
                self.logger.error('Not connected. Call login() first.')
                raise password_admin.exceptions.DbConnectionError(detail='Not connected. Call login() first.')

            search_filter = self._combine_filter(credentials.username)
            self.connection.search(
                search_base=self.config_data.base_dn,
                search_filter=search_filter,
            )

            if not self.connection.entries:
                self.logger.error(f'No user found with identifier: {credentials.username}')
                raise password_admin.exceptions.SessionNotFoundError(detail=f'No user found with identifier: {credentials.username}')

            if len(self.connection.entries) > 1:
                self.logger.error(f'Multiple users found with identifier: {credentials.username}')
                raise password_admin.exceptions.SessionNotFoundError(detail=f'Multiple users found with identifier: {credentials.username}')

            user_dn = self.connection.entries[0].entry_dn
            self.logger.info(f'Modifying password for DN: {user_dn}, attribute: {self.config_data.password_atribute}')
            self.connection.modify(user_dn, {self.config_data.password_atribute: [(MODIFY_REPLACE, [credentials.password])]})
            if self.connection.result['result'] == 0:
                self.logger.info(f'Successfully updated password for {credentials.username}')
            else:
                self.logger.error(f'Modify operation failed: {self.connection.result}')
                raise password_admin.exceptions.DbQueryError(detail=f'Modify operation failed: {self.connection.result}')

        except (password_admin.exceptions.DbConnectionError, password_admin.exceptions.SessionNotFoundError):
            raise
        except LDAPException as e:
            self.logger.error(f'Error editing user: {e}')
            raise password_admin.exceptions.DbQueryError(detail=f'Error editing user: {str(e)}')

    def logout(self) -> None:
        """Closes the connection to the LDAP server.

        Unbinds the current connection, releasing resources. The connection must be established
        and bound before calling this method.

        Raises:
            password_admin.exceptions.DbConnectionError: If unbinding the connection fails (e.g., server issues).
        """
        try:
            if self.connection and self.connection.bound:
                self.connection.unbind()
                self.logger.info('Successfully disconnected from LDAP server')
                self.connection = None
            else:
                self.logger.info('Logout not needed')
        except LDAPException as e:
            self.logger.error(f'Logout error: {e}')
            raise password_admin.exceptions.DbConnectionError(detail=f'Logout error: {str(e)}')

    def _combine_filter(self, value: str) -> str:
        """Combines the configured search filter with a specific user identifier.

        Args:
            value (str): The user identifier to include in the filter (e.g., username).

        Returns:
            str: The combined LDAP search filter (e.g., '(&(objectClass=person)(uid=jdoe))').
        """
        return f'(&{self.config_data.search_filter}({self.config_data.name_attribute}={value}))'
