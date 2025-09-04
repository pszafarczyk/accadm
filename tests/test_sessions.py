import time

from fastapi import status
import pytest

from password_admin.auth import LoginCredentials
from password_admin.database.factory import DbConnectionFactory
from password_admin.exceptions import DbConnectionError
from password_admin.exceptions import DbLoginError
from password_admin.exceptions import SessionNotFoundError
from password_admin.sessions import SessionStore
from password_admin.settings import SessionSettings
from tests.dummy_database import DummyDbConfig
from tests.dummy_database import DummyDbConnection


@pytest.fixture(autouse=True)
def patch_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patches Factory for every test to return DummyDbConnection."""

    def mock_create(self: DbConnectionFactory) -> DummyDbConnection:
        return DummyDbConnection(config=self._DbConnectionFactory__config)  # type: ignore[attr-defined]

    monkeypatch.setattr(DbConnectionFactory, 'create', mock_create)


@pytest.fixture
def db_config(request: pytest.FixtureRequest) -> DummyDbConfig:
    """Fixture returning dummy db config with requested settings."""
    param = getattr(request, 'param', {})
    return DummyDbConfig(**param)


@pytest.fixture
def db_factory(db_config: DummyDbConfig) -> DbConnectionFactory:
    """Fixture returning db factory for creating dummy database."""
    return DbConnectionFactory(config=db_config)


@pytest.fixture
def session_store(db_factory: DbConnectionFactory) -> SessionStore:
    """Fixture returning session store."""
    return SessionStore(SessionSettings(), db_factory)


@pytest.fixture
def credentials() -> LoginCredentials:
    """Fixture returning login credentials."""
    return LoginCredentials(username='user', password='pass')


@pytest.mark.parametrize('db_config', [{}], indirect=True)
def test_create_creates_db_connection(db_config: DummyDbConfig, session_store: SessionStore, credentials: LoginCredentials) -> None:
    """Creating session creates database connection."""
    session_store.create_session(credentials)
    connection_created = db_config.memory.object_created
    assert connection_created


@pytest.mark.parametrize('db_config', [{}], indirect=True)
def test_create_calls_loggin(db_config: DummyDbConfig, session_store: SessionStore, credentials: LoginCredentials) -> None:
    """Creating session loggs to database."""
    session_store.create_session(credentials)
    loggin_called = db_config.memory.login_call_amount > 0
    assert loggin_called


def test_create_returns_valid_session_id(session_store: SessionStore, credentials: LoginCredentials) -> None:
    """Creating session returns session_id after successful login."""
    session_id = session_store.create_session(credentials)
    assert isinstance(session_id, str)
    assert session_id


@pytest.mark.parametrize('db_config', [{'login_successful': False}], indirect=True)
def test_create_after_unsuccessful_login_raises(session_store: SessionStore, credentials: LoginCredentials) -> None:
    """Creating session raises after unsuccessful login."""
    with pytest.raises(DbLoginError, match='Login failed', check=lambda e: e.status_code == status.HTTP_401_UNAUTHORIZED):
        session_store.create_session(credentials)


@pytest.mark.parametrize('db_config', [{'login_connection_problem': True}], indirect=True)
def test_create_after_connection_problem_raises(session_store: SessionStore, credentials: LoginCredentials) -> None:
    """Creating session raises after connection problem."""
    with pytest.raises(DbConnectionError, match='Communication error', check=lambda e: e.status_code == status.HTTP_503_SERVICE_UNAVAILABLE):
        session_store.create_session(credentials)


def test_create_twice_creates_distinct_ids(session_store: SessionStore, credentials: LoginCredentials) -> None:
    """Creating session twice for same credentials creates distinct ids."""
    session_id1 = session_store.create_session(credentials)
    session_id2 = session_store.create_session(credentials)
    assert session_id1 != session_id2


def test_destroy_nonexisting_does_not_raise(session_store: SessionStore) -> None:
    """Destroying non-existing session does not raise."""
    session_store.destroy_session('1')


@pytest.mark.parametrize('db_config', [{}], indirect=True)
def test_destroy_calls_logout(db_config: DummyDbConfig, session_store: SessionStore, credentials: LoginCredentials) -> None:
    """Destroying session loggs out from database."""
    session_id = session_store.create_session(credentials)
    session_store.destroy_session(session_id)
    logout_called = db_config.memory.logout_call_amount > 0
    assert logout_called


@pytest.mark.parametrize('db_config', [{'logout_connection_problem': True}], indirect=True)
def test_destroy_after_connection_problem_does_not_raise(session_store: SessionStore, credentials: LoginCredentials) -> None:
    """Destroying session with db connection problem does not raise."""
    session_id = session_store.create_session(credentials)
    session_store.destroy_session(session_id)


def test_destroy_destroyed_does_not_raise(session_store: SessionStore, credentials: LoginCredentials) -> None:
    """Destroying destroyed session does not raise."""
    session_id = session_store.create_session(credentials)
    session_store.destroy_session(session_id)
    session_store.destroy_session(session_id)


def test_destroy_does_not_destroy_another(session_store: SessionStore, credentials: LoginCredentials) -> None:
    """Destroying session does not destroy another."""
    session_id1 = session_store.create_session(credentials)
    session_id2 = session_store.create_session(credentials)
    session_store.destroy_session(session_id1)
    db_connection2 = session_store.get_db_connection(session_id2)
    assert db_connection2


def test_get_after_successful_create_returns_connection(session_store: SessionStore, credentials: LoginCredentials) -> None:
    """Possible to get db connection after successful session creation."""
    session_id = session_store.create_session(credentials)
    db_connection = session_store.get_db_connection(session_id)
    assert isinstance(db_connection, DummyDbConnection)


def test_get_after_get_for_same_id_returns_connection(session_store: SessionStore, credentials: LoginCredentials) -> None:
    """Possible to get db connection more than once."""
    session_id = session_store.create_session(credentials)
    session_store.get_db_connection(session_id)
    db_connection2 = session_store.get_db_connection(session_id)
    assert isinstance(db_connection2, DummyDbConnection)


def test_get_for_same_id_returns_same_connection(session_store: SessionStore, credentials: LoginCredentials) -> None:
    """Multiple get for same id returns same db connection."""
    session_id = session_store.create_session(credentials)
    db_connection1 = session_store.get_db_connection(session_id)
    db_connection2 = session_store.get_db_connection(session_id)
    assert db_connection2 is db_connection1


def test_get_for_never_created_session_raises(session_store: SessionStore) -> None:
    """Getting never created session raises."""
    with pytest.raises(SessionNotFoundError, match='Session not found', check=lambda e: e.status_code == status.HTTP_401_UNAUTHORIZED):
        session_store.get_db_connection(session_id='1')


def test_get_after_destroy_raises(session_store: SessionStore, credentials: LoginCredentials) -> None:
    """Getting session after destroying raises."""
    session_id = session_store.create_session(credentials)
    session_store.destroy_session(session_id)
    with pytest.raises(SessionNotFoundError, match='Session not found', check=lambda e: e.status_code == status.HTTP_401_UNAUTHORIZED):
        session_store.get_db_connection(session_id)


def test_get_after_expire_raises(db_factory: DbConnectionFactory, credentials: LoginCredentials) -> None:
    """Getting expired session raises."""
    session_settings = SessionSettings(duration_seconds=1)
    session_store = SessionStore(session_settings, db_factory)
    session_id = session_store.create_session(credentials)
    time.sleep(2)
    with pytest.raises(SessionNotFoundError, match='Session not found', check=lambda e: e.status_code == status.HTTP_401_UNAUTHORIZED):
        session_store.get_db_connection(session_id)
