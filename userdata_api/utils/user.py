from functools import wraps
from typing import Awaitable, Callable, TypeVar

from fastapi import FastAPI
from fastapi_sqlalchemy import db
from sqlalchemy.orm import Session
from starlette.requests import Request
from typing_extensions import ParamSpec

from userdata_api.models.db import Info, Param, Source, Type
from userdata_api.schemas.user import user_interface


async def get_user_info(
    session: Session, user_id: int, user: dict[str, int | list[dict[str, str | int]]]
) -> dict[str, dict[str, str]]:
    """
    Получить пользоватеские данные, в зависимости от переданных скоупов.
    :param user: Сессия запрашиваемого данные
    :param session: Соеденение с БД
    :param user_id: Айди овнера информации(пользователя)
    :return: Словарь пользовательских данных, которым есть доступ у токена
    """
    infos: list[Info] = Info.query(session=session).filter(Info.owner_id == user_id).all()
    param_dict: dict[Param, list[Info]] = {}
    scope_names = [scope["name"] for scope in user["session_scopes"]]
    for info in infos:
        info_scopes = [scope.name for scope in info.scopes]
        ## Проверка доступов - нужен либо скоуп на категориию либо нуужно быть овнером информации
        if not all(scope in scope_names for scope in info_scopes) and user_id != user["user_id"]:
            continue
        if info.param not in param_dict.keys():
            param_dict[info.param] = []
        param_dict[info.param].append(info)
    result = {}
    for param, v in param_dict.items():
        if param.category.name not in result.keys():
            result[param.category.name] = {}
        if param.type == Type.ALL:
            result[param.category.name][param.name] = [_v.value for _v in v]
        elif param.type == Type.LAST:
            q: Info = (
                Info.query(session=session)
                .filter(Info.owner_id == user_id, Info.param_id == param.id)
                .order_by(Info.modify_ts.desc())
                .first()
            )
            result[param.category.name][param.name] = q.value
        elif param.type == Type.MOST_TRUSTED:
            q: Info = (
                Info.query(session=session)
                .join(Source)
                .filter(Info.owner_id == user_id, Info.param_id == param.id)
                .order_by(Source.trust_level.desc())
                .order_by(Info.modify_ts.desc())
                .first()
            )
            result[param.category.name][param.name] = q.value
    return result


T = TypeVar("T")
P = ParamSpec("P")


def refreshing(fn: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
    """
    Декоратор сообщает, что функция обновляет возможные поля пользователя.
    Обновляет поля пользователя в запросах (например, в ручке `GET /user/{user_id}`) и документацию OpenAPI
    Первым аргументом ручки должен быть request.
    """

    @wraps(fn)
    async def decorated(request: Request, *args: P.args, **kwargs: P.kwargs) -> T:
        app: FastAPI = request.app
        _res = await fn(request, *args, **kwargs)
        await user_interface.refresh(db.session)
        app.openapi_schema = None
        return _res

    return decorated
