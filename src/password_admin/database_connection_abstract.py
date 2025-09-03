from typing import Protocol, Any, TypeVar
from pydantic.dataclasses import dataclass


@dataclass
class DatabaseConfig:
    host: str
    port: int


TConfig = TypeVar('TConfig', bound=DatabaseConfig)


class DatabaseConnectionAbstract(Protocol[TConfig]):
    def config(self, config: TConfig) -> None: ...
    def login(self, *args: Any, **kwargs: Any) -> None: ...
    def get_users(self, *args: Any, **kwargs: Any) -> list[dict]: ...
    def logout(self) -> None: ...
    def change_pass(self, *args: Any, **kwargs: Any) -> None: ...
