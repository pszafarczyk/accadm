from ldap3 import Server, Connection, MODIFY_REPLACE, ALL, Tls


class DatabaseConnectionLdap:
    """A class to manage connections and operations with an OpenLDAP server."""

    def __init__(self):
        """Initialize the LDAP connection attributes."""
        self.server = None
        self.connection = None
        self.config_data = {}

    def config(self, server_address, base_dn):
        """Configure the LDAP server connection parameters.

        Args:
            server_address (str): LDAP server address (e.g., 'ldap://localhost:389' or 'ldaps://ldap.example.com:636').
            base_dn (str): Base DN for searches (e.g., 'dc=example,dc=com').

        Returns:
            bool: True if configuration is successful, False otherwise.
        """
        try:
            self.config_data = {'server_address': server_address, 'base_dn': base_dn}
            # Configure TLS if SSL is enabled
            self.server = Server(server_address, get_info=ALL)
            return True
        except Exception as e:
            print(f'Configuration error: {e}')
            return False

    def login(self, bind_dn, bind_password):
        """Establish a connection and bind to the LDAP server.

        Args:
            bind_dn (str): Bind DN for authentication (e.g., 'cn=admin,dc=example,dc=com').
            bind_password (str): Password for the bind DN.

        Returns:
            bool: True if login is successful, False otherwise.
        """
        try:
            if not self.server:
                raise ValueError('Server not configured. Call config() first.')
            self.connection = Connection(self.server, user=bind_dn, password=bind_password, auto_bind=True)
            print('Successfully connected to LDAP server.')
            return True
        except Exception as e:
            print(f'Login error: {e}')
            return False

    def get_users(self, attributes=None):
        """Retrieve users from the LDAP server.

        Args:
            attributes (list): List of attributes to retrieve (e.g., ['cn', 'uid']).
                              Defaults to ['cn', 'uid', 'mail'] if None.

        Returns:
            list: List of dictionaries containing user attributes, or empty list on error.
        """
        try:
            if not self.connection or not self.connection.bound:
                raise ValueError('Not connected. Call login() first.')

            # Default attributes if none provided
            if attributes is None:
                attributes = ['cn', 'uid', 'mail', 'userPassword']

            # Perform the search
            self.connection.search(
                search_base=self.config_data['base_dn'],
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

    def change_field(self, dn, field_name, data):
        """Update a specific field for a user in the PostgreSQL database.

        Args:
            user (str or int): The value of the user identifier (e.g., user ID or username).
            field_name (str): The name of the field/column to update (e.g., 'email').
            data (str): The new value for the field.
            table_name (str): Name of the table containing user data (default: 'users').
            user_identifier (str): The column name used to identify the user (default: 'id').

        Returns:
            bool: True if the update is successful, False otherwise.
        """
        try:
            if not self.connection or not self.connection.bound:
                raise ValueError('Not connected. Call login() first.')

            self.connection.modify(dn, {field_name: [(MODIFY_REPLACE, [data])]})

        except Exception as e:
            print(f'Error editing user: {e}')
            return []

    def change_pass(self, dn, data):
        self.change_field(dn, 'userPassword', data)

    def logout(self):
        """Close the connection to the LDAP server.

        Returns:
            bool: True if logout is successful, False otherwise.
        """
        try:
            if self.connection and self.connection.bound:
                self.connection.unbind()
                print('Successfully disconnected from LDAP server.')
                self.connection = None
                return True
            return False
        except Exception as e:
            print(f'Logout error: {e}')
            return False
