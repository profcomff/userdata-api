from __future__ import annotations

from fastapi_sqlalchemy import db
from sqlalchemy import not_

from userdata_api.exceptions import Forbidden, ObjectNotFound
from userdata_api.models.db import Category, Info, Param, Source, ViewType
from userdata_api.schemas.user import UserInfoGet, UserInfoUpdate


async def patch_user_info(
    new: UserInfoUpdate, user_id: int, user: dict[str, int | list[dict[str, str | int]]]
) -> UserInfoGet:
    scope_names = tuple(scope["name"] for scope in user["session_scopes"])
    if new.source == "admin" and "userdata.info.admin" not in scope_names:
        raise Forbidden(f"Admin source requires 'userdata.info.admin' scope")
    if new.source != "admin" and new.source != "user":
        raise Forbidden("HTTP protocol applying only 'admin' and 'user' source")
    if new.source == "user" and user["user_id"] != user_id:
        raise Forbidden(f"'user' source requires information own")
    for item in new.items:
        param = (
            db.session.query(Param)
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
            raise ObjectNotFound(Param, item.param)
        if param.category.update_scope not in scope_names and not (new.source == "user" and user["user_id"] == user_id):
            db.session.rollback()
            raise Forbidden(f"Updating category {param.category.name=} requires {param.category.update_scope=} scope")
        info = (
            db.session.query(Info)
            .join(Source)
            .filter(
                Info.param_id == param.id, Info.owner_id == user_id, Source.name == new.source, not_(Info.is_deleted)
            )
            .one_or_none()
        )
        if not info and item.value is None:
            continue
        if not info:
            Info.create(
                session=db.session,
                owner_id=user_id,
                param_id=param.id,
                source_id=db.session.query(Source).filter(Source.name == new.source).one_or_none().id,
                value=item.value,
            )
            continue
        if item.value is not None:
            if not param.changeable and "userdata.info.update" not in scope_names:
                db.session.rollback()
                raise Forbidden(f"Param {param.name=} change requires 'userdata.info.update' scope")
            info.value = item.value
            db.session.commit()
            continue
        info.is_deleted = True
        db.session.flush()
        continue
    return await get_user_info(user_id, user)


async def get_user_info(user_id: int, user: dict[str, int | list[dict[str, str | int]]]) -> UserInfoGet:
    infos: list[Info] = Info.query(session=db.session).filter(Info.owner_id == user_id).all()
    scope_names = [scope["name"] for scope in user["session_scopes"]]
    param_dict: dict[Param, list[Info] | Info | None] = {}
    for info in infos:
        ## Проверка доступов - нужен либо скоуп на категориию либо нужно быть овнером информации
        if info.category.read_scope and info.category.read_scope not in scope_names and user["user_id"] != user_id:
            continue
        if info.param not in param_dict.keys():
            param_dict[info.param] = [] if info.param.pytype == list[str] else None
        if info.param.type == ViewType.ALL:
            param_dict[info.param].append(info)
        elif (param_dict[info.param] is None) or (
            (info.param.type == ViewType.LAST and info.create_ts > param_dict[info.param].create_ts)
            or (
                info.param.type == ViewType.MOST_TRUSTED
                and (
                    param_dict[info.param].source.trust_level < info.source.trust_level
                    or (
                        param_dict[info.param].source.trust_level <= info.source.trust_level
                        and info.create_ts > param_dict[info.param].create_ts
                    )
                )
            )
        ):
            param_dict[info.param] = info
    result = []
    for item in param_dict.values():
        if isinstance(item, list):
            result.extend(
                [{"category": _item.category.name, "param": _item.param.name, "value": _item.value} for _item in item]
            )
        else:
            result.append({"category": item.category.name, "param": item.param.name, "value": item.value})
    return UserInfoGet(items=result)
