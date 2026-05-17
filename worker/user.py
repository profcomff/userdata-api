import logging

import sqlalchemy.orm
from event_schema.auth import UserLogin
from sqlalchemy import not_

from userdata_api.models.db import Info, Source
from userdata_api.utils.param_alias import get_param_by_name_or_alias


log = logging.getLogger(__name__)


def patch_user_info(new: UserLogin, user_id: int, *, session: sqlalchemy.orm.Session) -> None:
    for item in new.items:
        param = get_param_by_name_or_alias(
            session=session,
            category_name=item.category,
            param_name=item.param,
            source_name=new.source,
        )
        if not param:
            session.rollback()
            log.error(f"Param {item.param=} not found")
            return
        info = (
            session.query(Info)
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
            source = Source.query(session=session).filter(Source.name == new.source).one_or_none()
            if not source:
                session.rollback()
                log.warning(f"Source {new.source=} not found")
                return
            Info.create(
                session=session,
                owner_id=user_id,
                param_id=param.id,
                source_id=source.id,
                value=item.value,
            )
            continue
        if item.value is not None:
            info.value = item.value
            session.flush()
            continue
        if item.value is None:
            info.is_deleted = True
            session.flush()
            continue
