from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from settings import get_settings


settings = get_settings()


__all__ = ["PgSession"]


class PgSession:
    _engine = create_engine(str(settings.DB_DSN), pool_pre_ping=True)
    _Session = sessionmaker(bind=_engine)
    commit_on_exit: bool = True

    def __init__(self, commit_on_exit: bool = True) -> None:
        self.commit_on_exit = commit_on_exit

    def __enter__(self) -> Session:
        self._session = self._Session()
        return self._session

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.commit_on_exit:
            self._session.commit()
        self._session.close()
