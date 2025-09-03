from .database_connection_ldap import DatabaseConnectionLdap, LdapConfig
from .database_connection_postgress import DatabaseConnectionPostgres, PostgreConfig
from .database_connection_abstract import DatabaseConnectionAbstract, DatabaseConfig


def get_connection(config: DatabaseConfig) -> DatabaseConnectionAbstract:
    if type(config) is LdapConfig:
        database_connection = DatabaseConnectionLdap(config)
        return database_connection
    elif type(config) is PostgreConfig:
        database_connection = DatabaseConnectionPostgres(config)
        return database_connection
    else:
        raise ValueError(f'Unsupported config type: {type(config)}')
