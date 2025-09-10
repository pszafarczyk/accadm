from typing import Annotated

from pydantic import Field
from pydantic import StringConstraints

from password_admin.database.config import DbConfig


class LdapConfig(DbConfig):
    """LDAP related settings.

    An administrator can log in as admin@domain. With the default settings this
    gives the bind_dn cn=admin,ou=domain,dc=example,dc=net.
    Setting admin_rdn_separator to '' disables spliting of the login.
    An administrator can see a list of name_attribute of all objects under base_dn
    meeting search_filer for which has permissions. Objects are searched with the
    scope 'sub'.
    """

    dsn: Annotated[
        str,
        Field(
            description='LDAP connection string with no dn or search criteria',
            examples='ldap://localhost:1389, ldaps://192.168.0.1',
            pattern=r'^ldaps?://[a-zA-Z0-9.-]+(:[0-9]+)?$',  # IPv6?
        ),
    ] = 'ldap://localhost:389'
    use_ssl: bool = False
    use_starttls: bool = False
    base_bind_dn: Annotated[str, StringConstraints(min_length=1)] = 'cn=admin,dc=test,dc=org'
    # validation? https://stackoverflow.com/questions/9289357/javascript-regular-expression-for-dn
    admin_rdn_attribute: Annotated[str, StringConstraints(min_length=1)] = 'cn'
    admin_rdn_container_attribute: str = 'ou'
    admin_rdn_separator: Annotated[str, Field(description='String used to split login')] = '@'
    base_dn: Annotated[str, StringConstraints(min_length=1)] = 'dc=test,dc=org'
    search_filter: Annotated[str, StringConstraints(min_length=1)] = '(&(objectclass=inetOrgPerson)(mail=*))'  # + pattern
    name_attribute: Annotated[str, StringConstraints(min_length=1)] = 'mail'
    password_atribute: Annotated[str, StringConstraints(min_length=1)] = 'userPassword'  # noqa: S105
