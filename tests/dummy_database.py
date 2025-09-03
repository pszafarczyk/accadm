from password_admin.auth import LoginCredentials
from password_admin.auth import NewCredentials
from password_admin.database.config import DbConfig
from password_admin.exceptions import DbConnectionError
from password_admin.exceptions import DbLoginError
from password_admin.exceptions import DbQueryError


class DummyDbConfig(DbConfig):
    """Configuration for DummyDbConnection."""

    number_of_users: int = 1
    login_successful: bool = True
    login_connection_problem: bool = False
    logout_connection_problem: bool = False
    get_users_connection_problem: bool = False
    get_users_query_problem: bool = False
    set_password_connection_problem: bool = False
    set_password_query_problem: bool = False


class DummyDbConnection:
    """Database for tests."""

    def __init__(self, configuration: DummyDbConfig):
        self.__configuration = configuration
        self.logged_in = False
        self.password_changed = False

    def login(self, credentials: LoginCredentials) -> None:
        if self.__configuration.login_connection_problem:
            raise DbConnectionError
        if not self.__configuration.login_successful:
            raise DbLoginError(username=credentials.username)
        self.logged_in = True

    def logout(self) -> None:
        if self.__configuration.logout_connection_problem:
            raise DbConnectionError
        self.logged_in = False

    def get_users(self) -> list[str]:
        if self.__configuration.get_users_connection_problem:
            raise DbConnectionError
        if self.__configuration.get_users_query_problem:
            raise DbQueryError
        return ['user'] * self.__configuration.number_of_users

    def set_password(self, credentials: NewCredentials) -> None:  # noqa: ARG002
        if self.__configuration.set_password_connection_problem:
            raise DbConnectionError
        if self.__configuration.set_password_query_problem:
            raise DbQueryError
        self.password_changed = True
