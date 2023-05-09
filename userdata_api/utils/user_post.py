from __future__ import annotations

import dataclasses

from fastapi_sqlalchemy import db
from sqlalchemy.orm import Session

from userdata_api.exceptions import Forbidden, ObjectNotFound
from userdata_api.models.db import Category, Info, Param, Source


@dataclasses.dataclass
class QueryData:
    category_map: dict[str, Category]
    param_map: dict[str, dict[str, Param]]
    info_map: dict[tuple[int, int], Info]
    source: Source


async def __param(
    user_id: int, category: Category, query_data: QueryData, *, param_name: str, value: str | None
) -> None:
    param: Param = query_data.param_map.get(category.name).get(param_name, None)
    if not param:
        raise_exc(db.session, ObjectNotFound(Param, param_name))
    info = query_data.info_map.get((param.id, query_data.source.id), None)
    if not info:
        Info.create(
            session=db.session,
            owner_id=user_id,
            param_id=param.id,
            source_id=query_data.source.id,
            value=value,
        )
        return
    if value is not None:
        info.value = value
        return
    info.is_deleted = True
    db.session.flush()
    return


async def __category(
    user_id: int,
    category: Category,
    category_dict: dict[str, str],
    query_data: QueryData,
    user: dict[str, int | list[dict[str, str | int]]],
):
    scope_names = tuple(scope["name"] for scope in user["session_scopes"])
    for k, v in category_dict.items():
        param = query_data.param_map.get(category.name).get(k, None)
        if not param:
            db.session.rollback()
            raise ObjectNotFound(Param, k)
        if not param.changeable and "userdata.info.update" not in scope_names:
            db.session.rollback()
            raise Forbidden(f"Param {param.name=} change requires 'userdata.info.update' scope")
        await __param(user_id, category, query_data, param_name=k, value=v)


async def make_query(user_id: int, model: dict[str, dict[str, str] | int]) -> QueryData:
    param_map, category_map = {}, {}
    info_map = {}
    info_filter = []
    categories = Category.query(session=db.session).filter(Category.name.in_(model.keys())).all()
    for category in categories:
        category_map[category.name] = category
        param_map[category.name] = {param.name: param for param in category.params}
        info_filter.extend([param.id for param in category.params])
    source = Source.query(session=db.session).filter(Source.name == model["source"]).one_or_none()
    infos = Info.query(session=db.session).filter(Info.param_id.in_(info_filter), Info.owner_id == user_id).all()
    for info in infos:
        info_map[(info.param.id, info.source_id)] = info
    return QueryData(category_map=category_map, param_map=param_map, source=source, info_map=info_map)


def raise_exc(session: Session, exc: Exception):
    session.rollback()
    raise exc


async def post_model(
    user_id: int,
    model: dict[str, dict[str, str] | int],
    query_data: QueryData,
    user: dict[str, int | list[dict[str, str | int]]],
    session: Session,
):
    scope_names = tuple(scope["name"] for scope in user["session_scopes"])
    for k, v in model.items():
        if k == "source":
            continue
        category = query_data.category_map.get(k, None)
        if not category:
            raise_exc(session, ObjectNotFound(Category, k))
        if category.update_scope not in scope_names and not (model["source"] == "user" and user["user_id"] == user_id):
            raise_exc(session, Forbidden(f"Updating category {category.name=} requires {category.update_scope=} scope"))
        await __category(user_id, category, v, query_data, user)


async def process_post_model(
    user_id: int,
    model: dict[str, dict[str, str] | int],
    user: dict[str, int | list[dict[str, str | int]]],
):
    scope_names = tuple(scope["name"] for scope in user["session_scopes"])
    query_data = await make_query(user_id, model)
    if model["source"] == "admin" and "userdata.info.admin" not in scope_names:
        raise Forbidden(f"Admin source requires 'userdata.info.update' scope")
    if model["source"] != "admin" and model["source"] != "user":
        raise Forbidden("HTTP protocol applying only 'admin' and 'user' source")
    if model["source"] == "user" and user["user_id"] != user_id:
        raise Forbidden(f"'user' source requires information own")
    return await post_model(user_id, model, query_data, user, db.session)
