from typing import Protocol, Any
from pydantic.dataclasses import dataclass


@dataclass
class DatabaseConfig:
    host: str
    port: int


class DatabaseConnectionAbstract(Protocol):
    def login(self, *args: Any, **kwargs: Any) -> None: ...
    def get_users(self, *args: Any, **kwargs: Any) -> list[dict]: ...
    def logout(self) -> None: ...
    def change_pass(self, *args: Any, **kwargs: Any) -> None: ...
