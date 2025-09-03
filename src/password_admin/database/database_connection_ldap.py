from ldap3 import Server, Connection, MODIFY_REPLACE, ALL, Tls
from password_admin.database_connection_abstract import DatabaseConfig
from pydantic.dataclasses import dataclass


@dataclass
class LdapConfig(DatabaseConfig):
    """Configuration settings for LDAP server connection.

    Attributes:
        base_dn (str): The base Distinguished Name (DN) for LDAP searches (e.g., 'dc=example,dc=com').
        host (str): The hostname or IP address of the LDAP server (inherited from DatabaseConfig).
        port (int): The port number for the LDAP server (inherited from DatabaseConfig).
    """

    base_dn: str


class DatabaseConnectionLdap:
    """A class to manage connections and operations with an OpenLDAP server.

    This class provides methods to configure, connect, query, and modify data on an LDAP server
    using the ldap3 library. It handles user authentication, retrieval of user attributes,
    and field updates, including password changes.

    Attributes:
        server (ldap3.Server): The LDAP server object, initialized during configuration.
        connection (ldap3.Connection): The active connection to the LDAP server.
        config_data (LdapConfig): Configuration data for the LDAP server connection.
    """

    def __init__(self):
        """Initialize the LDAP connection attributes.

        Sets up the initial state with no server or connection established.
        Configuration must be provided using the `config` method before operations.
        """
        self.server = None
        self.connection = None
        self.config_data: LdapConfig

    def config(self, config: LdapConfig) -> None:
        """Configure the LDAP server connection parameters.

        Sets up the LDAP server with the provided configuration, including host, port,
        and base DN. Prepares the server for connection but does not establish it.

        Args:
            config (LdapConfig): Configuration object containing LDAP server details.

        Returns:
            bool: True if configuration is successful, False otherwise.

        Raises:
            Exception: If the configuration fails due to invalid parameters or server issues.
        """
        try:
            self.config_data = config
            # Configure TLS if SSL is enabled
            self.server = Server(host=self.config_data.host, port=self.config_data.port, get_info=ALL)
        except Exception as e:
            print(f'Configuration error: {e}')

    def login(self, bind_dn, bind_password) -> None:
        """Establish a connection and bind to the LDAP server.

        Authenticates to the LDAP server using the provided bind DN and password.
        The server must be configured using `config` before calling this method.

        Args:
            bind_dn (str): The Distinguished Name for authentication (e.g., 'cn=admin,dc=example,dc=com').
            bind_password (str): The password for the bind DN.

        Raises:
            ValueError: If the server is not configured (i.e., `config` was not called).
            Exception: If the connection or authentication fails.
        """
        try:
            if not self.server:
                raise ValueError('Server not configured. Call config() first.')
            self.connection = Connection(self.server, user=bind_dn, password=bind_password, auto_bind=True)
            print('Successfully connected to LDAP server.')
        except Exception as e:
            print(f'Login error: {e}')

    def get_users(self, attributes=None) -> list[dict]:
        """Retrieve user entries from the LDAP server.

        Queries the LDAP server for user entries matching the 'inetOrgPerson' object class
        under the configured base DN. Returns a list of dictionaries with the requested attributes.

        Args:
            attributes (list[str], optional): List of attributes to retrieve (e.g., ['cn', 'uid']).
                Defaults to ['cn', 'uid', 'mail', 'userPassword'] if None.

        Returns:
            list[dict]: A list of dictionaries, each containing the requested attributes for a user.
                Returns an empty list if no users are found or an error occurs.

        Raises:
            ValueError: If the connection is not established or bound (i.e., `login` was not called).
            Exception: If the search operation fails.
        """
        try:
            if not self.connection or not self.connection.bound:
                raise ValueError('Not connected. Call login() first.')

            # Default attributes if none provided
            if attributes is None:
                attributes = ['cn', 'uid', 'mail', 'userPassword']

            # Perform the search
            self.connection.search(
                search_base=self.config_data.base_dn,
                search_filter='(objectClass=inetOrgPerson)',  # Common filter for users
                attributes=attributes,
            )

            # Convert entries to a list of dictionaries
            users = []
            for entry in self.connection.entries:
                user_data = {attr: entry[attr].values for attr in attributes if attr in entry}
                users.append(user_data)

            return users
        except Exception as e:
            print(f'Error retrieving users: {e}')
            return []

    def _change_field(self, dn, field_name, data) -> None:
        """Update a specific field for a user in the LDAP server.

        Modifies a single attribute for the specified user identified by their Distinguished Name (DN).
        Uses the MODIFY_REPLACE operation to update the field with the provided data.

        Args:
            dn (str): The Distinguished Name of the user to update (e.g., 'uid=jdoe,dc=example,dc=com').
            field_name (str): The name of the attribute to update (e.g., 'mail').
            data (str): The new value for the attribute.

        Raises:
            ValueError: If the connection is not established or bound (i.e., `login` was not called).
            Exception: If the modification operation fails.

        Note:
            The method currently prints an error and returns an empty list on failure, which is inconsistent
            with the return type. This should be updated to return False for consistency.
        """
        try:
            if not self.connection or not self.connection.bound:
                raise ValueError('Not connected. Call login() first.')

            self.connection.modify(dn, {field_name: [(MODIFY_REPLACE, [data])]})

        except Exception as e:
            print(f'Error editing user: {e}')

    def change_pass(self, dn, new_pass) -> None:
        """Update the password for a user in the LDAP server.

        A convenience method to update the 'userPassword' attribute for the specified user.

        Args:
            dn (str): The Distinguished Name of the user (e.g., 'uid=jdoe,dc=example,dc=com').
            new_pass (str): The new password for the user.

        Returns:
            bool: True if the password update is successful, False otherwise.

        Raises:
            ValueError: If the connection is not established or bound (i.e., `login` was not called).
            Exception: If the password modification fails.
        """
        self._change_field(dn, 'userPassword', new_pass)

    def logout(self) -> None:
        """Close the connection to the LDAP server.

        Unbinds the current connection, effectively logging out and releasing resources.
        The connection must be established and bound before calling this method.

        Returns:
            bool: True if the disconnection is successful, False if no connection exists or an error occurs.

        Raises:
            Exception: If unbinding the connection fails.
        """
        try:
            if self.connection and self.connection.bound:
                self.connection.unbind()
                print('Successfully disconnected from LDAP server.')
                self.connection = None
            else:
                print(f'Logout not needed')
        except Exception as e:
            print(f'Logout error: {e}')
