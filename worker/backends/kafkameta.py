import logging
from abc import ABC, abstractmethod

from event_schema.auth import UserLogin
from sqlalchemy import not_

from userdata_api.models.db import Category, Info, Param, Source
from worker.backends.pg import PgSession


log = logging.getLogger(__name__)


class KafkaMeta(ABC):
    _pg = PgSession()

    @abstractmethod
    def __init__(self):
        raise NotImplementedError()

    @abstractmethod
    def run(self) -> None:
        raise NotImplementedError()

    def _patch_user_info(self, new: UserLogin, user_id: int) -> None:
        with self._pg as pg:
            for item in new.items:
                param = (
                    pg.query(Param)
                    .join(Category)
                    .filter(
                        Param.name == item.param,
                        Category.name == item.category,
                        not_(Param.is_deleted),
                        not_(Category.is_deleted),
                    )
                    .one_or_none()
                )
                if not param:
                    pg.rollback()
                    log.error(f"Param {item.param=} not found")
                    return
                info = (
                    pg.query(Info)
                    .join(Source)
                    .filter(
                        Info.param_id == param.id,
                        Info.owner_id == user_id,
                        Source.name == new.source,
                        not_(Info.is_deleted),
                    )
                    .one_or_none()
                )
                if not info and item.value is None:
                    continue
                if not info:
                    source = Source.query(session=pg).filter(Source.name == new.source).one_or_none()
                    if not source:
                        pg.rollback()
                        log.warning(f"Source {new.source=} not found")
                        return
                    Info.create(
                        session=pg,
                        owner_id=user_id,
                        param_id=param.id,
                        source_id=source.id,
                        value=item.value,
                    )
                    continue
                if item.value is not None:
                    info.value = item.value
                    pg.flush()
                    continue
                if item.value is None:
                    info.is_deleted = True
                    pg.flush()
                    continue
