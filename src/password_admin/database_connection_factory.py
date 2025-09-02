from typing import Literal
from .database_connection_ldap import DatabaseConnectionLdap
from .database_connection_postgress import DatabaseConnectionPostgres
from .database_connection_abstract import DatabaseConnectionAbstract


def get_connection(db_type: Literal['ldap', 'postgres']) -> DatabaseConnectionAbstract:
    if db_type == 'ldap':
        return DatabaseConnectionLdap()
    elif db_type == 'postgres':
        return DatabaseConnectionPostgres()
