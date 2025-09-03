import psycopg2
from psycopg2 import sql
from password_admin.database_connection_abstract import DatabaseConfig
from pydantic.dataclasses import dataclass


@dataclass
class PostgreConfig(DatabaseConfig):
    dbname: str


class DatabaseConnectionPostgres:
    """A class to manage connections and operations with a PostgreSQL database."""

    def __init__(self):
        """Initialize the PostgreSQL connection attributes."""
        self.connection = None
        self.cursor = None
        self.config_data: PostgreConfig

    def config(self, config: PostgreConfig) -> None:
        """Configure the PostgreSQL database connection parameters.

        Args:
            host (str): Database host address (e.g., 'localhost').
            dbname (str): Name of the database to connect to.
            port (int): Database port (default: 5432).

        Returns:
            bool: True if configuration is successful, False otherwise.
        """
        try:
            self.config_data = config
        except Exception as e:
            print(f'Configuration error: {e}')

    def login(self, user, password) -> None:
        """Establish a connection to the PostgreSQL database.

        Args:
            user (str): Username for authentication.
            password (str): Password for the user.

        Returns:
            bool: True if login is successful, False otherwise.
        """
        try:
            self.connection = psycopg2.connect(
                host=self.config_data.host,
                port=self.config_data.port,
                dbname=self.config_data.dbname,
                user=user,
                password=password,
            )
            self.cursor = self.connection.cursor()
            print('Successfully connected to PostgreSQL database.')
        except psycopg2.Error as e:
            print(f'Login error: {e}')

    def get_users(self, attributes=None, table_name='users') -> list[dict]:
        """Retrieve users from a specified table in the PostgreSQL database.

        Assumes a table with user data (e.g., columns like 'id', 'username', 'email').

        Args:
            attributes (list): List of column names to retrieve (e.g., ['username', 'email']).
                              Defaults to ['id', 'username', 'email'] if None.
            table_name (str): Name of the table containing user data (default: 'users').

        Returns:
            list: List of dictionaries containing user attributes, or empty list on error.
        """
        try:
            if not self.connection or not self.cursor:
                raise ValueError('Not connected. Call login() first.')

            # Default attributes if none provided
            if attributes is None:
                attributes = ['id', 'username', 'email', 'password']

            # Build the SQL
            query = sql.SQL('SELECT {} FROM {}').format(sql.SQL(', ').join(map(sql.Identifier, attributes)), sql.Identifier(table_name))

            # Execute the query
            self.cursor.execute(query)
            rows = self.cursor.fetchall()

            # Convert rows to a list of dictionaries
            users = []
            for row in rows:
                user_data = dict(zip(attributes, row))
                users.append(user_data)

            return users
        except psycopg2.Error as e:
            print(f'Error retrieving users: {e}')
            return []

    def logout(self) -> None:
        """Close the connection to the PostgreSQL database.

        Returns:
            bool: True if logout is successful, False otherwise.
        """
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
                print('Successfully disconnected from PostgreSQL database.')
                self.connection = None
                self.cursor = None
                return True
            return False
        except psycopg2.Error as e:
            print(f'Logout error: {e}')
            return False

    def change_field(self, user, field_name, data, table_name='users', user_identifier='id') -> None:
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
            if not self.connection or not self.cursor:
                raise ValueError('Not connected. Call login() first.')

            # Build the SQL UPDATE query safely
            query = sql.SQL('UPDATE {} SET {} = {} WHERE {} = {}').format(
                sql.Identifier(table_name), sql.Identifier(field_name), sql.Placeholder(), sql.Identifier(user_identifier), sql.Placeholder()
            )

            # Execute the query
            self.cursor.execute(query, (data, user))
            self.connection.commit()

            # Check if any rows were affected
            if self.cursor.rowcount > 0:
                print(f'Successfully updated {field_name} for user {user}')
            else:
                print(f'No user found with {user_identifier} = {user}')
        except psycopg2.Error as e:
            print(f'Error updating field: {e}')
            # self.connection.rollback()

    def change_pass(self, user, new_pass) -> None:
        self.change_field(user=user, field_name='password', data=new_pass)
