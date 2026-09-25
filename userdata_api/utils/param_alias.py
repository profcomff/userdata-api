from sqlalchemy import not_, or_
from sqlalchemy.orm import Session

from userdata_api.models.db import Category, Param, ParamAlias, Source


def get_param_by_name_or_alias(
    *,
    session: Session,
    category_name: str,
    param_name: str,
    source_name: str,
) -> Param | None:
    """
    Находит параметр сначала по каноническому имени, затем по алиасу.

    Если у алиаса source_id = NULL, алиас считается общим для всех источников.
    """
    param = (
        session.query(Param)
        .join(Category)
        .filter(
            Param.name == param_name,
            Category.name == category_name,
            not_(Param.is_deleted),
            not_(Category.is_deleted),
        )
        .one_or_none()
    )
    if param:
        return param

    source = Source.query(session=session).filter(Source.name == source_name).one_or_none()
    source_id = source.id if source else None

    query = (
        session.query(Param)
        .join(Category)
        .join(ParamAlias, ParamAlias.param_id == Param.id)
        .filter(
            ParamAlias.name == param_name,
            Category.name == category_name,
            not_(ParamAlias.is_deleted),
            not_(Param.is_deleted),
            not_(Category.is_deleted),
        )
    )
    if source_id is None:
        query = query.filter(ParamAlias.source_id.is_(None))
    else:
        query = query.filter(or_(ParamAlias.source_id == source_id, ParamAlias.source_id.is_(None)))
    return query.one_or_none()
