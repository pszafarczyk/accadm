import logging
from pydantic import ValidationError
from password_admin.database.factory import DbConnectionFactory
from password_admin.database.ldap.config import LdapConfig
from password_admin.database.postgres.config import PostgresConfig
from password_admin.auth import LoginCredentials, NewCredentials
import password_admin.exceptions
from pydantic import PostgresDsn


def test_connections():
    """Tests LDAP and PostgreSQL database connections using the DbConnectionFactory.

    Configures and tests connections to both LDAP and PostgreSQL databases sequentially.
    Performs login, user retrieval, password update, and logout operations for each database.
    Logs all operations and errors using the Python logging module.
    """
    logger = logging.getLogger(__name__)

    test_ldap(logger)
    test_postgres(logger)


def test_ldap(logger):
    try:
        ldap_config = LdapConfig(
            dsn='ldap://localhost:389', base_dn='dc=test,dc=org', name_attribute='uid', password_atribute='userPassword', base_bind_dn='dc=test,dc=org'
        )
        logger.info('LDAP configuration initialized')

        # Create LDAP connection via factory
        factory = DbConnectionFactory(config=ldap_config)
        ldap_conn = factory.create()
        logger.info('LDAP connection created via factory')

        # Test LDAP operations
        test_database_operations(
            ldap_conn, 'LDAP', LoginCredentials(username='admin', password='admin'), NewCredentials(username='jane', password='limpamponi1234567890#'), logger
        )

    except password_admin.exceptions.DbConnectionError as e:
        logger.error(f'LDAP connection error: {e.detail}')
        raise
    except password_admin.exceptions.DbLoginError as e:
        logger.error(f'LDAP login error: {e.detail}')
        raise
    except password_admin.exceptions.DbQueryError as e:
        logger.error(f'LDAP query error: {e.detail}')
        raise
    except password_admin.exceptions.SessionNotFoundError as e:
        logger.error(f'LDAP user not found error: {e.detail}')
        raise
    except Exception as e:
        logger.error(f'Unexpected LDAP error: {str(e)}')
        raise


def test_postgres(logger):
    try:
        dsn = PostgresDsn(url='postgresql://localhost:5432/testdb')
        postgres_config = PostgresConfig(
            dsn=dsn,
            users_query='SELECT username FROM users',
            password_query='UPDATE users SET password = %s WHERE username = %s',
        )
        logger.info('PostgreSQL configuration initialized')

        # Create PostgreSQL connection via factory
        factory = DbConnectionFactory(config=postgres_config)
        postgres_conn = factory.create()
        logger.info('PostgreSQL connection created via factory')

        # Test PostgreSQL operations
        test_database_operations(
            postgres_conn,
            'PostgreSQL',
            LoginCredentials(username='testuser', password='testpassword'),
            NewCredentials(username='bob1', password='limpamponi1234567890#'),
            logger,
        )

    except ValidationError as e:
        logger.error(f'PostgreSQL configuration error: {e}')
        raise
    except password_admin.exceptions.DbConnectionError as e:
        logger.error(f'PostgreSQL connection error: {e.detail}')
        raise
    except password_admin.exceptions.DbLoginError as e:
        logger.error(f'PostgreSQL login error: {e.detail}')
        raise
    except password_admin.exceptions.DbQueryError as e:
        logger.error(f'PostgreSQL query error: {e.detail}')
        raise
    except password_admin.exceptions.SessionNotFoundError as e:
        logger.error(f'PostgreSQL user not found error: {e.detail}')
        raise
    except Exception as e:
        logger.error(f'Unexpected PostgreSQL error: {str(e)}')
        raise


def test_database_operations(db_conn, db_type: str, login_credentials: LoginCredentials, new_credentials: NewCredentials, logger: logging.Logger):
    """Performs standard database operations (login, get users, set password, logout) for a given connection.

    Args:
        db_conn: The database connection object implementing DbConnectionInterface.
        db_type (str): The type of database (e.g., 'LDAP', 'PostgreSQL') for logging purposes.
        login_credentials (LoginCredentials): Credentials for logging into the database.
        new_credentials (NewCredentials): Credentials for updating a user's password.
        logger (logging.Logger): Logger instance for recording operations and errors.
    """
    # Login
    logger.info(f'[{db_type}] Logging in to database')
    db_conn.login(login_credentials)

    # Retrieve and log users
    logger.info(f'[{db_type}] Retrieving users')
    users = db_conn.get_users()
    for user in users:
        logger.info(f'[{db_type}] User: {user}')

    # Update password
    logger.info(f'[{db_type}] Attempting to update password for user: {new_credentials.username}')
    db_conn.set_password(new_credentials)

    # Verify users again
    logger.info(f'[{db_type}] Retrieving users after password update')
    users = db_conn.get_users()
    for user in users:
        logger.info(f'[{db_type}] User: {user}')

    # Logout
    db_conn.logout()
    logger.info(f'[{db_type}] Logged out from database')


if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()],
    )
    test_connections()
