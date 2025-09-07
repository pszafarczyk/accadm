from pydantic import BaseModel

from password_admin.auth import LoginCredentials
from password_admin.auth import NewCredentials
from password_admin.database.config import DbConfig
from password_admin.exceptions import DbConnectionError
from password_admin.exceptions import DbLoginError
from password_admin.exceptions import DbQueryError


class DummyDbMemory(BaseModel):
    """Storage to read information from dummy db operations."""

    object_created: bool = False
    login_call_amount: int = 0
    logged_in: bool | None = None
    logout_call_amount: int = 0
    getusers_call_amount: int = 0
    setpassword_call_mount: int = 0
    password_changed: bool | None = None


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
    memory: DummyDbMemory = DummyDbMemory()


class DummyDbConnection:
    """Database for tests."""

    def __init__(self, config: DummyDbConfig):
        self.__config = config
        self.__config.memory.object_created = True

    def login(self, credentials: LoginCredentials) -> None:
        self.__config.memory.login_call_amount += 1
        if self.__config.login_connection_problem:
            raise DbConnectionError
        if not self.__config.login_successful:
            raise DbLoginError(username=credentials.username)
        self.__config.memory.logged_in = True

    def logout(self) -> None:
        self.__config.memory.logout_call_amount += 1
        if self.__config.logout_connection_problem:
            raise DbConnectionError
        self.__config.memory.logged_in = False

    def get_users(self) -> list[str]:
        self.__config.memory.getusers_call_amount += 1
        if self.__config.get_users_connection_problem:
            raise DbConnectionError
        if self.__config.get_users_query_problem:
            raise DbQueryError
        return ['user'] * self.__config.number_of_users

    def set_password(self, credentials: NewCredentials) -> None:  # noqa: ARG002
        self.__config.memory.setpassword_call_mount += 1
        if self.__config.set_password_connection_problem:
            raise DbConnectionError
        if self.__config.set_password_query_problem:
            raise DbQueryError
        self.__config.memory.password_changed = True
